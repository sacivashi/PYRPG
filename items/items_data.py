from util.file_io import get_data, read_csv

STAT_COLUMNS = ['Strength', 'Agility', 'Intelligence', 'Defense', 'Magic', 'Luck']


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
    return {stat: int(row[stat]) for stat in STAT_COLUMNS if row.get(stat) is not None}


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


def get_droppable_items():
    """(name, rarity) pairs for every item eligible to drop as loot — rarity used as drop weight."""
    return [(name, get_item_rarity(name)) for name in get_item_names() if is_item_droppable(name)]


def is_item_consumable(name):
    """Whether the item is used-and-removed rather than equipped. Defaults to False if no Consumable column exists yet."""
    return _is_yes(name, "Consumable")


PRICE_PIVOT_RARITY = 65  # fixed reference point — adding a very common item no longer reprices the whole shop


def get_item_price(name):
    """Gold cost, derived from Rarity so there's one source of truth: rarer (lower weight) items
    cost more, floored at 15 so even the most common items aren't free: max(15, int(abs(65 - rarity) * 0.65))."""
    rarity = get_item_rarity(name)
    return max(15, int(abs(PRICE_PIVOT_RARITY - rarity) * 0.65))


def get_buyable_items():
    """(name, price) pairs for every item currently stocked in the shop."""
    return [(name, get_item_price(name)) for name in get_item_names() if is_item_buyable(name)]
