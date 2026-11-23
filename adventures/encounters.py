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


# --- wandering merchants (and thieves dressed as one) ------------------------------------------

MERCHANT_STOCK_SIZE = 3
MERCHANT_RARE_CHANCE = 35   # % a merchant also carries one item the shop never sells
SELL_RATE = 0.35            # merchants buy your loot for int(35% of its price)


def parse_multiplier(cell):
    """'*=1.3' -> 1.3, '' -> 1"""
    match = re.search(r"\*=?\s*(\d+(?:\.\d+)?)", cell or "")
    return float(match.group(1)) if match else 1.0


def base_price(game, item_name):
    """What the shop would ask for it: the always-stocked price for potions, otherwise by rarity"""
    from items.items_data import get_item_price
    return dict(game.ALWAYS_STOCKED).get(item_name, get_item_price(item_name))


def sell_price(game, item_name):
    return int(base_price(game, item_name) * SELL_RATE)


def merchant_stock():
    """A few shop items, and sometimes one rare item the shop never sells (droppable but not
    buyable, weighted by Rarity like a drop). [(name, base price), ...]"""
    from items.items_data import get_buyable_items, get_droppable_items, is_item_buyable, get_item_price
    shop = get_buyable_items()
    stock = random.sample(shop, min(MERCHANT_STOCK_SIZE, len(shop)))
    rares = [(name, rarity) for name, rarity in get_droppable_items() if not is_item_buyable(name)]
    if rares and random.randint(1, 100) <= MERCHANT_RARE_CHANCE:
        names, weights = zip(*rares)
        rare = random.choices(names, weights=weights, k=1)[0]
        stock.append((rare, get_item_price(rare)))
    return stock


def merchant_price(game, row, base):
    """base * the row's Cost markup (*=1.3), swayed by Charisma if the row's Charisma_effect says so"""
    price = int(base * parse_multiplier(row.get("Cost")))
    if (row.get("Charisma_effect") or "").strip().lower() == "yes":
        from util.charisma import charisma_price
        price = charisma_price(price, game._charisma())
    return price


def merchant(game, row):
    """Buy from a small stock at the row's markup, or sell your loot for 35% of its price.
    A thief merchant (the row's Enemy_spawn) looks exactly the same until you trade: it pockets
    your gold (or your item) and surprise-attacks. Beat it and you get back what you gave it
    (the gold, not the item you paid for). Thieves grow with depth like Mimics.
    Returns "left", or the thief fight's result."""
    pd = game.player_data
    thief = parse_spawn(row.get("Enemy_spawn"))
    stock = [(name, merchant_price(game, row, base)) for name, base in merchant_stock()]
    sold_out = set()

    print("\nAs you walk by, there seems to be a wandering merchant.")
    first_impression(game, row)

    while True:
        print("\n=== Wandering Merchant ===")
        print(f"Gold: {pd.gold}")
        for i, (name, price) in enumerate(stock, 1):
            print(f"  [{i}] {name} - {'SOLD OUT' if i - 1 in sold_out else f'{price} gold'}")
        print("  [s] Sell loot")
        print("  [0] Leave")
        choice = input("\nBuy a number, 'c' + number to check its stats (e.g. c1), s to sell, or 0 to leave: ").strip().lower()

        if choice in ("0", ""):
            print("You nod to the merchant and move on.")
            return "left"
        if choice == "s":
            sold = _sell_to_merchant(game)
            if sold and thief:
                return _thief_strikes(game, thief, item=sold)
            if sold:
                pd.gold += sell_price(game, sold)
                print(f"Sold {sold} for {sell_price(game, sold)} gold.")
            continue
        if choice.startswith("c"):
            index = _pick(choice[1:], len(stock))
            if index is not None:
                game._print_item_stats(stock[index][0])
                input("\nPress Enter to continue...")
            continue

        index = _pick(choice, len(stock))
        if index is None:
            print("Invalid choice.")
            continue
        if index in sold_out:
            print("That one's already sold.")
            continue
        name, price = stock[index]
        if pd.gold < price:
            print("You don't have enough gold.")
            continue
        pd.gold -= price
        if thief:
            return _thief_strikes(game, thief, gold=price)
        pd.loot.append(name)
        sold_out.add(index)
        print(f"Bought {name} for {price} gold.")


def _pick(text, count):
    """'2' -> 1 if there are at least 2 entries, otherwise None"""
    text = text.strip()
    if not text.isdigit() or not 1 <= int(text) <= count:
        return None
    return int(text) - 1


def _sell_to_merchant(game):
    """Pick one item from your loot and hand one copy over (unequipping it if it was the last one
    worn). Returns the item's name, or None. Paying for it is the merchant's business."""
    pd = game.player_data
    stacks = game._stacked_loot()
    if not stacks:
        print("You have nothing to sell.")
        return None
    print("\nWhat do you want to sell?")
    for i, (name, count) in enumerate(stacks, 1):
        print(f"  [{i}] {game._stack_label(name, count)} - {sell_price(game, name)} gold")
    index = _pick(input("Sell which? (0 to go back): "), len(stacks))
    if index is None:
        return None

    name = stacks[index][0]
    pd.loot.remove(name)
    if name == pd.equipped and name not in pd.loot:
        pd.equipped = None
        game._apply_equipment_hp_change()
    return name


def _thief_strikes(game, thief, gold=0, item=None):
    """The merchant was a thief: it keeps what you handed over and surprise-attacks. Win and you
    get it back."""
    pd = game.player_data
    name, size = spawn_name(thief[0]), thief[1]
    print(f"\nThe merchant's smile turns sharp. \"Pleasure doing business!\" It was a {name} all along!")

    def give_back():
        if gold:
            pd.gold += gold
            print(f"You take back your {gold} gold.")
        if item:
            pd.loot.append(item)
            print(f"You take back your {item}.")

    return game.fight(name, size, surprise=True, scaling=pd.distance - 1, on_victory=give_back)


# Encounter Type -> the function that runs it (Adventures and Events are looked up in ADVENTURES)
ENCOUNTER_TYPES = {"Chest": chest, "Healer": cook, "Merchant": merchant}


# --- prayer sculptures: boons & curses ----------------------------------------------------------

SCULPTURE_TYPES = {"Boon", "Curse"}
SCULPTURE_FAIL_CHANCE = 10  # % — the gods have their own reasons


def sculpture_fail_chance(charisma):
    """10%, minus the Charisma odds sway for +Charisma (down to 0), plus it for -Charisma (up to 30)"""
    sway = odds_sway_percent(charisma)
    return max(0, SCULPTURE_FAIL_CHANCE - sway) if charisma > 0 else SCULPTURE_FAIL_CHANCE + sway


def receive(game, row):
    """Start the row's boon or curse and say what it was. Of growth also heals you to its new max."""
    from util.effects import add_effect, describe, make_effect
    effect = make_effect(row)
    add_effect(game.player_data.effects, effect)
    game._refresh_max_hp()
    if effect["target"] == "max_hp":
        game.player_data.hp = game.player_data.max_hp
    if effect["kind"] == "Curse":
        print(f"A chill runs down your spine. You've been cursed: {describe(effect)}")
    else:
        print(f"Warmth fills you. You've been blessed: {describe(effect)}")
    return effect


def sculpture(game, row):
    """A prayer sculpture. Which god it belongs to (the row: a boon or a curse) you only find out
    after praying, and 10% of the time nothing answers. Returns the effect, or None."""
    print("\nAs you walk by, there seems to be an old prayer sculpture. You can't make out whose.")
    if input("Pray to it? (y/n) ").strip().lower() != "y":
        print("You leave the gods to themselves.")
        return None
    if random.randint(1, 100) <= sculpture_fail_chance(game._charisma()):
        print("You pray... and nothing answers. The gods have their own reasons.")
        input("\nPress Enter to continue...")
        return None
    effect = receive(game, row)
    input("\nPress Enter to continue...")
    return effect


def prayer_card(game):
    """The Prayer card: a random boon or curse, drawn the way sculptures are (Odds, with Charisma
    swaying the curses), no matter how deep you are. It never fails."""
    rows = [row for row in get_encounters() if row["Type"] in SCULPTURE_TYPES]
    weights = [weight(row, game._charisma()) for row in rows]
    print("You read the Prayer card out loud...")
    return receive(game, random.choices(rows, weights=weights, k=1)[0])


ENCOUNTER_TYPES.update({kind: sculpture for kind in SCULPTURE_TYPES})
