from items.items_data import get_item_stats, get_item_price, is_item_buyable, is_item_droppable


def test_get_item_stats_returns_all_stat_deltas_including_zero():
    # Iron Sword (v1.0): Strength 4, Agility 1, Defence 1, Luck 2, everything else 0 — all six
    # STAT_COLUMNS should come back, not just the non-zero ones.
    stats = get_item_stats("Iron Sword")
    assert stats == {
        'Strength': 4,
        'Agility': 1,
        'Intelligence': 0,
        'Defence': 1,
        'Magic': 0,
        'Luck': 2,
    }


def test_price_formula_pivots_on_rarity_65():
    # max(15, int(abs(65 - rarity) * 0.65)) — a very common item no longer reprices everything
    assert get_item_price("Wooden sword") == 15   # rarity 80 -> 9 -> floor
    assert get_item_price("Smart ring") == 21     # rarity 32
    assert get_item_price("Timer") == 32          # rarity 15
    assert get_item_price("Berserker armor") == 41  # rarity 1


def test_get_item_stats_unknown_item_returns_none():
    assert get_item_stats("Not A Real Item") is None


def test_common_item_is_cheaper_than_rare_item():
    # Starter gear (Rarity 60, the most common item) should always be cheaper
    # than Turtle Shell (Rarity 14, much rarer) — regardless of the exact
    # constants in the pricing formula, common must stay cheaper than rare.
    assert get_item_price("Starter gear") < get_item_price("Turtle Shell")


def test_price_never_drops_below_the_floor():
    # Every buyable item should cost at least 15 gold (the floor in get_item_price)
    assert get_item_price("Starter gear") >= 15


def test_buyable_flag_reads_correctly():
    assert is_item_buyable("Iron Sword") is True
    assert is_item_buyable("Bloody Crown") is False


def test_droppable_flag_reads_correctly():
    assert is_item_droppable("Bomb") is False
    assert is_item_droppable("Arcane Ring") is True
