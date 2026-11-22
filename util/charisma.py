"""Charisma: how easily you sway people. Unlike every other stat it never touches combat, encounter
matching or level-ups. It only changes how people treat you (patch_notes/version 1.0.5.md)."""

CHARISMA = "Charisma"
PRICE_SWAY_CAP = 15  # percent; reached at about +-31 Charisma


def price_sway_percent(charisma):
    """Percent a price moves: int(min(15, abs(cha) * 0.48)). Positive Charisma makes things cheaper,
    negative makes them pricier. The sign is applied by charisma_price()."""
    return int(min(PRICE_SWAY_CAP, abs(charisma) * 0.48))


def charisma_price(base, charisma):
    """What someone actually charges you for `base` gold"""
    percent = price_sway_percent(charisma)
    if base <= 0 or percent == 0:
        return base
    factor = 1 - percent / 100 if charisma > 0 else 1 + percent / 100
    return max(1, round(base * factor))
