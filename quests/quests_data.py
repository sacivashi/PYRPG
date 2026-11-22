from items.items_data import get_item_names
from util.file_io import get_data, read_csv

# data/quests.csv — one row per quest:
#   id          unique key; progress and completion are saved under it
#   title       shown on the quest board
#   type        what counts as progress — a QUEST_TYPES key below, or "spend"
#   target      what the type is matched against (see QUEST_TYPES); for "spend", the gold to give
#   amount      how many times it has to happen
#   reward      a number = gold, a perk name from PERKS below, an item name from items.csv, or 0 = nothing
#   charisma    how much Charisma completing it gives (+2) or takes (-3)
#   choice      button labels for a choice quest, e.g. Give/Take wallet (empty = no choice)
#   description shown on the quest board (quote it if it contains commas)
#   spawn       enemies you fight the moment you accept, e.g. Townfolk *3 (empty = none)
#
# Choice quests: target (spend only), reward and charisma can hold one value per choice, split by "/",
# in the same order as the choice labels (charity: 55/0, Dice machine/0, +2/-2, Accept/Decline).
# A single value applies to every choice.

# Event quest types: the game reports what happened with PYRPG.quest_event(type, value, amount),
# and each type decides whether that value counts toward a quest's target. Adding a type is one
# line here plus a quest_event() call wherever that thing happens.
QUEST_TYPES = {
    "defeat": lambda target, value: value.lower() == target.lower(),  # won a fight against enemy `value`
    "use":    lambda target, value: value.lower() == target.lower(),  # did action `value`, e.g. FAST_TRAVEL
    "reach":  lambda target, value: int(value) >= int(target),        # explored to depth `value` (fast travel doesn't count)
}
# "spend" isn't an event — it's paid at the quest board itself, the moment you make the choice
SUPPORTED_TYPES = set(QUEST_TYPES) | {"spend"}

# Non-gold rewards. Claiming one adds it to PlayerData.perks; whatever it affects uses it up.
PERKS = {
    "free_fast_travel": "your next fast travel is free",
}

# "use" quest targets the game reports
FAST_TRAVEL = "fast travel"


def _split(cell):
    """'55/0' -> ['55', '0'], 'Accept/"Decline"' -> ['Accept', 'Decline'], '' -> []"""
    if not cell or not cell.strip():
        return []
    return [part.strip().strip('"').strip() for part in cell.split("/")]


def _parse_reward(cell):
    """A number is gold (0 = no reward); anything else is a lowercase perk or item name"""
    cell = cell.strip()
    return int(cell) if cell.isdigit() else cell.lower()


def _parse_spawn(cell):
    """'Townfolk *3' -> ('Townfolk', 3), 'priest' -> ('priest', 1), '' -> None"""
    if not cell or not cell.strip():
        return None
    name, _, count = cell.partition("*")
    return name.strip(), int(count) if count.strip() else 1


def _options(quest):
    """One option per choice: {label, cost, reward, charisma}. A quest with no choice has one
    option whose label is None. A column with a single value applies to every option."""
    labels = _split(quest.get("choice"))
    costs = _split(quest["target"]) if quest["type"] == "spend" else []
    rewards = _split(quest["reward"]) or ["0"]
    charismas = _split(quest.get("charisma")) or ["0"]
    count = max(len(labels), len(costs), len(rewards), len(charismas), 1)

    def pick(values, i, default):
        if not values:
            return default
        return values[i] if i < len(values) else values[-1]

    return [{
        "label": pick(labels, i, None) if labels else None,
        "cost": int(pick(costs, i, "0")),
        "reward": _parse_reward(pick(rewards, i, "0")),
        "charisma": int(pick(charismas, i, "0")),
    } for i in range(count)]


def get_quests():
    """{quest_id: quest}, in file order. Each quest has title, type, target, amount, description,
    spawn ((name, count) or None) and options (see _options())."""
    quests = {}
    for row in read_csv(get_data("quests_csv")):
        quest = {column: (value or "").strip() for column, value in row.items() if column}
        quest["type"] = quest["type"].lower()
        quest["amount"] = int(quest["amount"])
        quest["spawn"] = _parse_spawn(quest.get("spawn"))
        quest["options"] = _options(quest)
        quests[quest.pop("id")] = quest
    return quests


def quest_unlocked(quest_id, completed_quests):
    """Quest chains: a quest named by an unlocks.csv row (unlocks = quest:<id>, type = quest) stays off
    the board until the quest in that row's target is completed. Any one such row is enough."""
    rows = [row for row in read_csv(get_data("unlocks_csv"))
            if (row.get("unlocks") or "").strip().lower() == f"quest:{quest_id}".lower()
            and (row.get("type") or "").strip().lower() == "quest"]
    if not rows:
        return True
    completed = {quest.lower() for quest in completed_quests}
    return any((row.get("target") or "").strip().lower() in completed for row in rows)


def reward_item(reward):
    """The items.csv name a reward refers to (rewards are stored lowercase), or None"""
    if isinstance(reward, int):
        return None
    return next((name for name in get_item_names() if name.lower() == reward), None)


def grant_reward(player_data, reward):
    """Gold goes to gold, an item into loot, anything else is a perk; 0 is nothing at all"""
    if isinstance(reward, int):
        player_data.gold += reward
    elif reward_item(reward):
        player_data.loot.append(reward_item(reward))
    else:
        player_data.perks.append(reward)


def describe_reward(reward):
    """How a reward reads on the board, or None when there's no reward (0)"""
    if isinstance(reward, int):
        return f"{reward} gold" if reward else None
    return PERKS.get(reward) or reward_item(reward) or reward


def quest_progress(quest_id, quest, quest_flags):
    """How far along a quest is, from the saved quest_flags. Saves from before quests.csv stored a
    finished defeat quest as {"defeated_<target>": True} — that still counts as complete."""
    if quest["type"] == "defeat" and quest_flags.get(f"defeated_{quest['target'].lower()}") is True:
        return quest["amount"]
    return min(quest["amount"], quest_flags.get(quest_id, 0))


def started_quests(completed_quests, quest_flags):
    """For saves from before quests were opt-in: every quest they had finished or made progress
    on counts as accepted, so nothing they were working on gets reset."""
    started = list(completed_quests)
    for quest_id, quest in get_quests().items():
        if quest_id not in started and quest_progress(quest_id, quest, quest_flags) > 0:
            started.append(quest_id)
    return started
