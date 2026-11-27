"""Unlocks (v1.0.7): classes, enemies, items and events you earn through tasks.

data/unlocks.csv lists them — `id, unlocks, type, target, amount, role, hint`. `unlocks` is what the
row unlocks (`class:knight`, `enemy:Cursed Human`, `item:Necronomicon`, `event:Halt!`); several rows
can unlock the same thing, and finishing any one of them is enough. `role` limits a row to one class
(`Mage`: only a mage's progress counts). `quest:` rows are quest chains — per character, handled by
quests_data.quest_unlocked(), not here.

Progress belongs to the player (v1.1.1; it was shared by everyone before): it lives in their
entry in data/players.json, next to their adventurers (players/profiles.py).

Two kinds of rows:
    counters    the game reports what happened with record(type, value, amount) and it adds up
                defeat      target = an enemy name, or "-lck" for any enemy with negative Luck
                defeated    being slain
                use         target = what was used (Sculpture: praying at one)
                charisma_quest  claiming a quest that gained you Charisma
                block       damage blocked by defending
                attack_heal HP healed from attacking (-Strength)
                mana_spent  mana spent on spells & abilities
                zeroed      enemy stats your curses brought down to 0
                encounter   target = an enemy, or blank for "the same enemy, any enemy" (its best count)
    thresholds  checked against your character with check_state()
                equip       target = an item you have equipped
                stat_below  target = a stat at or below `amount` (gear included)
                stat_above  target = a stat at or above `amount` (gear included)
                max_hp      max HP at or above `amount`
                quest       target = a quest id you've completed
Anything not unlocked by a row is never locked.
"""
from util.file_io import get_data, read_csv

THRESHOLD_TYPES = {"equip", "stat_below", "stat_above", "max_hp", "quest"}
CATEGORIES = [("class", "Classes"), ("enemy", "Enemies"), ("item", "Items"), ("event", "Events")]
# Unlocks that don't announce themselves, with the line they leave instead
QUIET = {"enemy": "...something followed you out of town.",
         "event": "...word about you has been getting around town."}


def get_unlock_rows():
    """Every global unlock row (quest chains left out), cleaned up: amount is an int (1 if blank)"""
    rows = []
    for row in read_csv(get_data("unlocks_csv")):
        row = {column: (value or "").strip() for column, value in row.items() if column}
        if not row.get("unlocks") or row["unlocks"].lower().startswith("quest:"):
            continue
        row["type"] = row["type"].lower()
        row["amount"] = int(row["amount"] or 1)
        rows.append(row)
    return rows


# --- progress (each player's own, v1.1.1) ----------------------------------------------------------

def load_progress():
    """{"progress": {row id: count, or {enemy: count} for blank-target encounters}, "unlocked": [keys]}"""
    from players.profiles import load_unlocks
    return load_unlocks()


def _save(data):
    from players.profiles import save_unlocks
    save_unlocks(data)


def unlocked_keys():
    return {key.lower() for key in load_progress()["unlocked"]}


def locked_keys():
    """Lowercase keys that some row unlocks and nobody has unlocked yet"""
    done = unlocked_keys()
    return {row["unlocks"].lower() for row in get_unlock_rows()} - done


def is_unlocked(key):
    return key.lower() not in locked_keys()


def grant(key):
    """Unlock something outright (tests, or a reward that hands one out directly)"""
    data = load_progress()
    if key.lower() not in {done.lower() for done in data["unlocked"]}:
        data["unlocked"].append(key)
        _save(data)


def locked_names(category):
    """The lowercase names still locked in a category: locked_names("enemy") -> {"cursed human", ...}"""
    prefix = f"{category}:"
    return {key[len(prefix):] for key in locked_keys() if key.startswith(prefix)}


# --- counting --------------------------------------------------------------------------------------

def _role_ok(row, role):
    return not row.get("role") or (role or "").lower() == row["role"].lower()


def _matches(row, value):
    target = row.get("target", "").lower()
    if not target:
        return True
    if row["type"] == "defeat" and target == "-lck":
        from enemies.enemies_data import get_enemy_stats
        stats = get_enemy_stats(str(value)) or {}
        return int(stats.get("Luck", 0) or 0) < 0
    return str(value).lower() == target


def row_progress(row, progress):
    """How far along a row is (its best count, for per-enemy encounters)"""
    value = progress.get(row["id"], 0)
    return max(value.values(), default=0) if isinstance(value, dict) else value


def record(kind, value=None, amount=1, role=None):
    """Something happened (`kind` is a counter type): count it toward every matching row and unlock
    whatever it finished. Returns the newly unlocked keys (already announced)."""
    if amount <= 0:
        return []
    data = load_progress()
    done = {key.lower() for key in data["unlocked"]}
    changed = False
    newly = []
    for row in get_unlock_rows():
        if row["type"] != kind or row["unlocks"].lower() in done or not _role_ok(row, role):
            continue
        if not _matches(row, value):
            continue
        if kind == "encounter" and not row.get("target"):
            counts = data["progress"].setdefault(row["id"], {})
            counts = counts if isinstance(counts, dict) else {}
            data["progress"][row["id"]] = counts
            counts[str(value)] = counts.get(str(value), 0) + amount
        else:
            data["progress"][row["id"]] = data["progress"].get(row["id"], 0) + amount
        changed = True
        if row_progress(row, data["progress"]) >= row["amount"]:
            data["unlocked"].append(row["unlocks"])
            done.add(row["unlocks"].lower())
            newly.append(row["unlocks"])
    if changed:
        _save(data)
    announce(newly)
    return newly


def _threshold_met(row, role, equipped, stats, max_hp, completed_quests):
    if not _role_ok(row, role):
        return False
    target = row.get("target", "")
    if row["type"] == "equip":
        return (equipped or "").lower() == target.lower()
    if row["type"] == "stat_below":
        return stats.get(target, 0) <= row["amount"]
    if row["type"] == "stat_above":
        return stats.get(target, 0) >= row["amount"]
    if row["type"] == "max_hp":
        return (max_hp or 0) >= row["amount"]
    if row["type"] == "quest":
        return target.lower() in {quest.lower() for quest in completed_quests}
    return False


def check_state(role, equipped=None, stats=None, max_hp=0, completed_quests=()):
    """Check the threshold rows against a character. Returns the newly unlocked keys (already announced)."""
    data = load_progress()
    done = {key.lower() for key in data["unlocked"]}
    newly = []
    for row in get_unlock_rows():
        if row["type"] not in THRESHOLD_TYPES or row["unlocks"].lower() in done:
            continue
        if _threshold_met(row, role, equipped, stats or {}, max_hp, completed_quests):
            data["unlocked"].append(row["unlocks"])
            done.add(row["unlocks"].lower())
            newly.append(row["unlocks"])
    if newly:
        _save(data)
    announce(newly)
    return newly


# --- showing it ----------------------------------------------------------------------------------------

def split_key(key):
    """"class:knight" -> ("class", "Knight"); names keep their case unless they're all lowercase"""
    category, _, name = key.partition(":")
    return category.lower(), (name.title() if name.islower() else name)


def announce(keys):
    for key in keys:
        category, name = split_key(key)
        print(QUIET[category] if category in QUIET else f"  ✦ Unlocked: {name} ✦")


def hint(row):
    """The row's hint, with its class requirement in front: "As a mage, defeat 15 enemies with -lck" """
    text = row.get("hint") or "???"
    if row.get("role"):
        return f"As a {row['role'].lower()}, {text[0].lower()}{text[1:]}"
    return text


def journal_lines():
    """The Journal: a summary line, then every category with what's unlocked and what isn't (yet)"""
    data = load_progress()
    done = {key.lower() for key in data["unlocked"]}
    rows = get_unlock_rows()
    by_key = {}
    for row in rows:
        by_key.setdefault(row["unlocks"], []).append(row)

    summary, sections = [], []
    for category, title in CATEGORIES:
        keys = [key for key in by_key if split_key(key)[0] == category]
        if not keys:
            continue
        got = sum(key.lower() in done for key in keys)
        summary.append(f"{title}   {got}/{len(keys)}")
        sections.append("")
        sections.append(f"[{title}]")
        for key in keys:
            if key.lower() in done:
                sections.append(f"  {split_key(key)[1]:<16} unlocked")
                continue
            for i, row in enumerate(by_key[key]):
                label = "???" if i == 0 else "  or"
                line = f"  {label:<16} {hint(row)}"
                if row["type"] not in THRESHOLD_TYPES and row["amount"] > 1:
                    line += f"   ({int(min(row['amount'], row_progress(row, data['progress'])))}/{row['amount']})"
                sections.append(line)
    return ["=== Journal ===", "   ".join(summary)] + sections


def locked_role_lines():
    """For class selection: one line per locked class, its hint(s) and progress"""
    data = load_progress()
    done = {key.lower() for key in data["unlocked"]}
    lines = []
    for row in get_unlock_rows():
        if split_key(row["unlocks"])[0] != "class" or row["unlocks"].lower() in done:
            continue
        line = f"  ???  {hint(row)}"
        if row["type"] not in THRESHOLD_TYPES and row["amount"] > 1:
            line += f"   ({int(min(row['amount'], row_progress(row, data['progress'])))}/{row['amount']})"
        lines.append(line)
    return lines
