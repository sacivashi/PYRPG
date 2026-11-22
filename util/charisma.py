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


ODDS_SWAY_CAP = 20  # percent; reached at +-80 Charisma


def odds_sway_percent(charisma):
    """Percent Charisma moves your odds with people and gods: int(min(20, abs(cha) * 0.25)).
    Positive Charisma makes good things likelier and bad ones rarer, negative the other way round."""
    return int(min(ODDS_SWAY_CAP, abs(charisma) * 0.25))


def charisma_range(low, high, charisma, ugly_only=False):
    """Where someone's price lands in a `low ~ high` range (the Cook's 1.5 ~ 2.3, Halt!'s 15 ~ 40).
    At 0 Charisma it's the middle; the prettier you are the closer to `low`, the uglier the closer
    to `high`, all the way there at the full price sway (about +-31 Charisma).
    `ugly_only` is for people who only deal with -Charisma players (Halt!'s guard): the whole range
    is spread over the ugly side instead, so just below 0 pays `low` and -31 or worse pays `high`."""
    pull = price_sway_percent(charisma) / PRICE_SWAY_CAP
    if ugly_only:
        return low + (high - low) * (pull if charisma < 0 else 0)
    middle = (low + high) / 2
    if charisma > 0:
        return middle - (middle - low) * pull
    return middle + (high - middle) * pull
