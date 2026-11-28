from util.charisma import CHARISMA
from util.file_io import get_data, read_csv

# The stats that level-ups, Sleight of stats and combat work with. Charisma isn't one of them: it only
# changes through quests and gear, so it's added separately for item deltas (ITEM_STAT_COLUMNS).
STAT_COLUMNS = ['Strength', 'Agility', 'Intelligence', 'Defense', 'Magic', 'Luck']
ITEM_STAT_COLUMNS = STAT_COLUMNS + [CHARISMA]


def _get_item_row(name):
    """The items.csv row for this item (matched case-insensitively), or None"""
    return next((row for row in read_csv(get_data("items_csv")) if row["Name"].lower() == name.lower()), None)


def _is_yes(name, column):
    """Whether the item's `column` says Yes. False for unknown items or a missing column."""
    row = _get_item_row(name)
    return bool(row and (row.get(column) or "").strip().lower() == "yes")


def get_item_names():
    return [row["Name"] for row in read_csv(get_data("items_csv"))]


def get_item_stats(name):
    """Stat deltas only — non-stat columns (e.g. Rarity) are excluded by name, not position."""
    row = _get_item_row(name)
    if row is None:
        return None
    return {stat: int(row[stat]) for stat in ITEM_STAT_COLUMNS if row.get(stat) is not None}


def get_item_rarity(name):
    """Drop weight — higher means more common. Defaults to 1 if no Rarity column exists yet."""
    row = _get_item_row(name)
    return int(row["Rarity"]) if row and row.get("Rarity") else 1


def is_item_buyable(name):
    """Whether the item can appear in the shop. Defaults to False if no Buyable column exists yet."""
    return _is_yes(name, "Buyable")


def is_item_droppable(name):
    """Whether the item can appear as a random loot drop. Defaults to False if no Droppable column exists yet."""
    return _is_yes(name, "Droppable")


def _unlocked(names):
    """Leave out items still locked (unlocks.csv `item:` rows) — they don't drop or sell until earned"""
    from unlocks.unlocks import locked_names
    locked = locked_names("item")
    return [name for name in names if name.lower() not in locked]


def get_droppable_items():
    """(name, rarity) pairs for every (unlocked) item eligible to drop as loot — rarity used as drop weight."""
    return [(name, get_item_rarity(name)) for name in _unlocked(get_item_names())
            if is_item_droppable(name) and has_price(name)]


def is_item_consumable(name):
    """Whether the item is used-and-removed rather than equipped. Defaults to False if no Consumable column exists yet."""
    return _is_yes(name, "Consumable")


PRICE_PIVOT_RARITY = 65  # fixed reference point — adding a very common item no longer reprices the whole shop
NO_PRICE = -1  # Rarity -1: a given item (Small bomb), worth nothing — never sold, bought by merchants, or dropped


def has_price(name):
    return get_item_rarity(name) != NO_PRICE


def get_item_price(name):
    """Gold cost, derived from Rarity so there's one source of truth: rarer (lower weight) items
    cost more, floored at 15 so even the most common items aren't free: max(15, int(abs(65 - rarity) * 0.65)).
    Rarity -1 (NO_PRICE) is worth 0."""
    if not has_price(name):
        return 0
    rarity = get_item_rarity(name)
    return max(15, int(abs(PRICE_PIVOT_RARITY - rarity) * 0.65))


def get_buyable_items():
    """(name, price) pairs for every (unlocked) item the shop can stock."""
    return [(name, get_item_price(name)) for name in _unlocked(get_item_names())
            if is_item_buyable(name) and has_price(name)]


def rarity_sample(items, k):
    """Pick k different (name, price) entries, weighted by Rarity like drops are: a Wooden sword (80)
    shows up far more often than a Rapier (3). Every item gets at least weight 1, so nothing buyable
    is impossible to find."""
    import random
    pool = list(items)
    picked = []
    while pool and len(picked) < k:
        weights = [max(1, get_item_rarity(name)) for name, _ in pool]
        choice = random.choices(range(len(pool)), weights=weights, k=1)[0]
        picked.append(pool.pop(choice))
    return picked
