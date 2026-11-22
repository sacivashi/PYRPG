"""Passive encounters (data/encounters.csv): everything you can run into out there that isn't just
a fight. explore() rolls one 25% of the time, return_to_town() rolls the town ones (Halt!).

What's eligible depends on the row's Depth (a number = that depth or deeper, `town` = only on the
way back to town), Charisma_req and HP_req (`<0`, `<=50%` of max HP, ...). Odds are weights among
whatever is eligible, except town rows, whose Odds are a straight % chance. Charisma sways the
odds of bad encounters (curses, thief merchants, Mimics): rarer the prettier you are."""
import random
import re

from adventures.adventures import ADVENTURES, parse_spawn, spawn_name
from util.charisma import CHARISMA, charisma_range, odds_sway_percent
from util.file_io import get_data, read_csv

PASSIVE_ENCOUNTER_CHANCE = 25  # % of explores that bring a passive encounter instead of a fight
TOWN = "town"

# A hidden bad one: the row looks like its good sibling (a chest, a merchant) but has an enemy in it
DISGUISED_TYPES = {"Chest", "Merchant"}
BAD_TYPES = {"Curse"}

NOTICE_CAP = 45            # % — reached at 27 Intelligence
FINE_FLAVOR_CHANCE = 25    # % chance of a "seems fine" line when nothing was noticed


def get_encounters():
    return read_csv(get_data("encounters_csv"))


def is_bad(row):
    return row["Type"] in BAD_TYPES or (row["Type"] in DISGUISED_TYPES and bool(parse_spawn(row.get("Enemy_spawn"))))


_REQUIREMENT = re.compile(r"^(<=|>=|<|>|=)?\s*(-?\d+(?:\.\d+)?)\s*(%)?$")


def meets(requirement, value, whole=None):
    """'<0', '>=5', '<=50%' (of `whole`), '' (no requirement) -> does `value` pass?"""
    requirement = (requirement or "").strip()
    if not requirement:
        return True
    match = _REQUIREMENT.match(requirement)
    if not match:
        raise ValueError(f"Can't read the requirement {requirement!r}")
    op, number, percent = match.groups()
    limit = float(number) * (whole or 0) / 100 if percent else float(number)
    return {"<": value < limit, "<=": value <= limit, ">": value > limit,
            ">=": value >= limit, "=": value == limit, None: value == limit}[op]


def handler(row):
    """The function that runs this row, or None if that kind of encounter isn't built yet"""
    if row["Type"] in ("Adventure", "Event"):
        return ADVENTURES.get(row["Description"])
    return ENCOUNTER_TYPES.get(row["Type"])


def eligible(game, row, in_town=False):
    depth = (row.get("Depth") or "").strip().lower()
    if (depth == TOWN) != in_town:
        return False
    if not in_town and game.player_data.distance < int(depth or 0):
        return False
    pd = game.player_data
    return (handler(row) is not None
            and meets(row.get("Charisma_req"), game._charisma())
            and meets(row.get("HP_req"), pd.hp, pd.max_hp))


def weight(row, charisma):
    """The row's Odds, with bad encounters swayed by Charisma: up to 20% rarer, or likelier"""
    odds = float(row.get("Odds") or 0)
    if not is_bad(row):
        return odds
    sway = odds_sway_percent(charisma) / 100
    return odds * (1 - sway if charisma > 0 else 1 + sway)


def roll_wild_encounter(game):
    """25% of the time, one eligible wild encounter (weighted by Odds), otherwise None"""
    if random.randint(1, 100) > PASSIVE_ENCOUNTER_CHANCE:
        return None
    rows = [row for row in get_encounters() if eligible(game, row)]
    weights = [weight(row, game._charisma()) for row in rows]
    if not rows or sum(weights) <= 0:
        return None
    return random.choices(rows, weights=weights, k=1)[0]


def roll_town_encounter(game):
    """Each eligible town row gets its own Odds% roll, first hit wins"""
    for row in get_encounters():
        if eligible(game, row, in_town=True) and random.uniform(0, 100) < weight(row, game._charisma()):
            return row
    return None


def run_encounter(game, row):
    return handler(row)(game, row)


# --- first impressions: Intelligence can tell a bad encounter -------------------------------------

NOTICE_FLAVOR = {
    "Merchant": [
        "This merchant seems cheeky to me..",
        "I got that gut feeling I shouldn't trust this one.",
        "This merchant's eyes seem to glint towards my pockets...",
        "I feel malicious intent..",
        "I don't like this one's face.",
        "Maybe, better not.",
        "With a squint of an eye, looks suspicious",
    ],
    "Chest": [
        "I think I just seen it lick its lid.",
        "I can hear a heartbeat.",
        "This chest has a soul to it, I know it.",
        "I know a Mimic when I see it!",
        "This one, don't open it.",
        "Oh believe me this chest has no gold or items...",
    ],
}
FINE_FLAVOR = [
    "Seems fine to me.",
    "Let's have a gander.",
    "Looks okay.",
    "Please be fine.",
    "Something with the script tells me, this one is good.",
]


def notice_chance(intelligence):
    """int(max(0, min(45, int * 1.7)))% to see through a disguised bad encounter"""
    return int(max(0, min(NOTICE_CAP, intelligence * 1.7)))


def first_impression(game, row):
    """Print what your gut says. Returns True if you saw through it (it's bad and you noticed)."""
    intelligence = game._effective_stats().get("Intelligence", 0)
    if is_bad(row) and random.randint(1, 100) <= notice_chance(intelligence):
        print(f'"{random.choice(NOTICE_FLAVOR[row["Type"]])}"')
        return True
    if random.randint(1, 100) <= FINE_FLAVOR_CHANCE:
        print(f'"{random.choice(FINE_FLAVOR)}"')
    return False


# --- chests and Mimics ----------------------------------------------------------------------------

MIMIC_BONUS_GOLD = (3, 11)


def chest(game, row):
    """A treasure chest, or a Mimic dressed as one (the row's Enemy_spawn). Opening a Mimic gets you
    surprise-attacked; beating it pays 3 ~ 11 bonus gold on top of the usual rewards. Mimics grow
    with depth (+depth - 1 to every stat above 0). Returns "chest", the fight's result, or None."""
    print("\nAs you walk by, there seems to be a treasure chest.")
    first_impression(game, row)
    if input("Do you open it? (y/n) ").strip().lower() != "y":
        print("You leave it be.")
        return None

    spawn = parse_spawn(row.get("Enemy_spawn"))
    if not spawn:
        game.open_chest()
        return "chest"

    name = spawn_name(spawn[0])
    print(f"\nThe lid creaks open... onto a row of teeth. It's a {name}!")

    def bonus_gold():
        gold = random.randint(*MIMIC_BONUS_GOLD)
        game.player_data.gold += gold
        print(f"Its belly held {gold} more gold!")

    return game.fight(name, 1, surprise=True, scaling=game.player_data.distance - 1, on_victory=bonus_gold)


# --- the Cook ----------------------------------------------------------------------------------

def parse_range(cell):
    """'v*1.5~2.3' -> (1.5, 2.3), '0/15~40' -> (15.0, 40.0): the last `low~high` in the cell"""
    match = re.findall(r"(-?\d+(?:\.\d+)?)\s*~\s*(-?\d+(?:\.\d+)?)", cell or "")
    if not match:
        raise ValueError(f"No low~high range in {cell!r}")
    low, high = match[-1]
    return float(low), float(high)


def swayed(row, low, high, game, ugly_only=False):
    """Where in low~high this row's price lands: by Charisma if the row's Charisma_effect says so"""
    if (row.get("Charisma_effect") or "").strip().lower() == "yes":
        return charisma_range(low, high, game._charisma(), ugly_only)
    return (low + high) / 2


def cook(game, row):
    """Buy as much of the missing HP as you like, at 1.5 ~ 2.3 gold per HP (the prettier you are,
    the cheaper). Returns the HP healed (0 if none)."""
    pd = game.player_data
    rate = swayed(row, *parse_range(row.get("Cost")), game)
    print("\nAs you walk by, a cook waves you over to a bubbling pot.")
    print(f'"Something warm for the road? {rate:.2f} gold a bowl-full of HP."')
    missing = pd.max_hp - pd.hp
    if missing <= 0:
        print("You're full of life already. You wave the cook off.")
        input("\nPress Enter to continue...")
        return 0

    affordable = min(missing, int(pd.gold / rate) if rate > 0 else missing)
    print(f"HP: {pd.hp}/{pd.max_hp}  Gold: {pd.gold}")
    if affordable <= 0:
        print("You can't afford even a spoonful.")
        input("\nPress Enter to continue...")
        return 0

    choice = input(f"How much HP? (1-{affordable}, 0 to leave): ").strip()
    amount = int(choice) if choice.isdigit() else 0
    if not 1 <= amount <= affordable:
        print("You thank the cook and move on.")
        input("\nPress Enter to continue...")
        return 0

    cost = int(amount * rate)
    pd.gold -= cost
    pd.hp += amount
    print(f"You pay {cost} gold and eat. Delicious! HP: {pd.hp}/{pd.max_hp}")
    input("\nPress Enter to continue...")
    return amount


# Encounter Type -> the function that runs it (Adventures and Events are looked up in ADVENTURES)
ENCOUNTER_TYPES = {"Chest": chest, "Healer": cook}
