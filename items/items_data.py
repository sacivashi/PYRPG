from util.file_io import get_data, read_csv

STAT_COLUMNS = ['Strength', 'Agility', 'Intelligence', 'Defence', 'Magic', 'Luck']


def get_item_names():
    reader = read_csv(get_data("items_csv"))
    return [row[0] for row in reader[1:] if row]


def get_item_stats(name):
    """Stat deltas only — non-stat columns (e.g. Rarity) are excluded by name, not position."""
    reader = read_csv(get_data("items_csv"))
    headers = reader[0]  # First row is the header
    for row in reader[1:]:  # Skip the header
        if row[0].lower() == name.lower():
            row_by_header = dict(zip(headers, row))
            return {stat: int(row_by_header[stat]) for stat in STAT_COLUMNS if stat in row_by_header}
    return None


def get_item_rarity(name):
    """Drop weight — higher means more common. Defaults to 1 if no Rarity column exists yet."""
    reader = read_csv(get_data("items_csv"))
    headers = reader[0]
    if "Rarity" not in headers:
        return 1
    for row in reader[1:]:
        if row[0].lower() == name.lower():
            row_by_header = dict(zip(headers, row))
            return int(row_by_header["Rarity"])
    return 1


def is_item_buyable(name):
    """Whether the item can appear in the shop. Defaults to False if no Buyable column exists yet."""
    reader = read_csv(get_data("items_csv"))
    headers = reader[0]
    if "Buyable" not in headers:
        return False
    for row in reader[1:]:
        if row[0].lower() == name.lower():
            row_by_header = dict(zip(headers, row))
            return row_by_header["Buyable"].strip().lower() == "yes"
    return False


def is_item_consumable(name):
    """Whether the item is used-and-removed rather than equipped. Defaults to False if no Consumable column exists yet."""
    reader = read_csv(get_data("items_csv"))
    headers = reader[0]
    if "Consumable" not in headers:
        return False
    for row in reader[1:]:
        if row[0].lower() == name.lower():
            row_by_header = dict(zip(headers, row))
            return row_by_header["Consumable"].strip().lower() == "yes"
    return False


def get_item_price(name):
    """Gold cost, derived from Rarity so there's one source of truth: price = round(500 / rarity)."""
    rarity = get_item_rarity(name)
    return round(500 / rarity) if rarity > 0 else 500


def get_buyable_items():
    """(name, price) pairs for every item currently stocked in the shop."""
    return [(name, get_item_price(name)) for name in get_item_names() if is_item_buyable(name)]
