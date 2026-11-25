"""Temporary effects: sculpture boons and curses (and the Prayer card). They sit on top of gear the
way gear sits on top of base stats: `stats` -> apply_equipment() -> apply_effects(). Nothing here
is ever saved (PlayerData.effects is marked saved=False), so a curse can never become permanent.

An effect is a dict built from an encounters.csv row by make_effect():
    {"name": "Of fear", "kind": "Curse", "target": "Charisma", "op": "-", "value": 999,
     "left": 5, "ticks_on": ["explore"]}
`target` is a stat (Strength, Charisma, ...) or one of the non-stat bonuses below. `left` counts
down each time one of its `ticks_on` events happens; at 0 the effect wears off."""
import re

from items.items_data import ITEM_STAT_COLUMNS

# Non-stat targets: what each one changes, and what uses it up (a 'Duration' of N = N of these)
BONUS_TICKS = {
    "rest_chance": ["rest"],          # every rest attempt out there
    "rest_restoration": ["rested"],   # every successful rest out there
    "gold": ["victory"],              # the next win(s)
    "EXP": ["victory"],
    "max_hp": ["victory"],
}
STAT_TICKS = ["explore"]              # stat effects with a Duration: that many explores
UNTIL_RESTED = ["rested", "town_rest"]  # no Duration: until a successful rest (or a rest in town)

_OP = re.compile(r"^\s*([+\-*])=\s*(-?\d+(?:\.\d+)?)\s*$")


def parse_op(cell):
    """'+=15' -> ('+', 15.0), '*=0' -> ('*', 0.0), '-=999' -> ('-', 999.0)"""
    match = _OP.match(cell or "")
    if not match:
        raise ValueError(f"Can't read the effect value {cell!r}")
    return match.group(1), float(match.group(2))


def make_effect(row):
    op, value = parse_op(row.get("Value"))
    target = (row.get("Effect") or "").strip()
    duration = (row.get("Duration") or "").strip()
    if target not in BONUS_TICKS and target not in ITEM_STAT_COLUMNS:
        raise ValueError(f"Unknown effect target {target!r} ({row.get('Description')})")
    if duration:
        ticks_on = BONUS_TICKS.get(target, STAT_TICKS)
        left = int(float(duration))
    else:
        ticks_on, left = UNTIL_RESTED, 1
    return {"name": row["Description"], "kind": row["Type"], "target": target, "op": op,
            "value": value, "left": left, "ticks_on": list(ticks_on)}


def _apply(value, effect):
    op, amount = effect["op"], effect["value"]
    if op == "+":
        return value + amount
    if op == "-":
        return value - amount
    return value * amount


def _whole(value):
    return int(value) if float(value).is_integer() else value


def apply_effects(stats, effects):
    """A copy of `stats` with every stat effect applied (Of crippling: Strength * 0)"""
    stats = dict(stats)
    for effect in effects or []:
        if effect["target"] in stats or effect["target"] in ITEM_STAT_COLUMNS:
            stats[effect["target"]] = _whole(_apply(stats.get(effect["target"], 0), effect))
    return stats


def bonus(effects, target, base):
    """`base` with every effect on a non-stat target applied: bonus(fx, "gold", 10) -> 11.2"""
    for effect in effects or []:
        if effect["target"] == target:
            base = _apply(base, effect)
    return base


def add_effect(effects, effect):
    """Praying to the same sculpture twice refreshes it instead of stacking"""
    effects[:] = [e for e in effects if e["name"] != effect["name"]]
    effects.append(effect)


def tick(effects, event):
    """Count `event` against every effect that wears off on it. Returns the effects that just ended."""
    ended = []
    for effect in effects:
        if event in effect["ticks_on"]:
            effect["left"] -= 1
            if effect["left"] <= 0:
                ended.append(effect)
    effects[:] = [e for e in effects if e not in ended]
    return ended


# How the non-stat targets read in plain words
BONUS_LABELS = {"rest_chance": "rest odds", "rest_restoration": "healing from rests",
                "gold": "gold from wins", "EXP": "EXP from wins", "max_hp": "max HP"}
TICK_UNITS = {"rest": "rest attempt", "rested": "successful rest", "victory": "win", "explore": "explore"}


def change_text(effect):
    """What the effect does, in words: '+15% rest odds', '+12% gold from wins', 'Strength drops to 0'"""
    op, value, target = effect["op"], effect["value"], effect["target"]
    label = BONUS_LABELS.get(target, target)
    if op == "*":
        if value == 0:
            return f"{label} drops to 0"
        return f"{_whole(round((value - 1) * 100, 1)):+}% {label}"
    sign = "+" if op == "+" else "-"
    if target == "rest_restoration":                      # a share of max HP & mana per rest
        return f"{sign}{_whole(round(value * 100, 1))}% {label}"
    if target == "rest_chance":
        return f"{sign}{_whole(value)}% {label}"
    return f"{sign}{_whole(value)} {label}"


def lasts_text(effect, upcoming=False):
    """How long it lasts: 'until you rest', '3 rest attempts left' (or 'for your next 3 rest attempts')"""
    if effect["ticks_on"] == UNTIL_RESTED:
        return "until you rest"
    left = effect["left"]
    unit = TICK_UNITS[effect["ticks_on"][0]] + ("s" if left != 1 else "")
    if upcoming:
        if effect["target"] == "max_hp":          # Of growth: the extra HP lasts until you win
            return "until your next win" if left == 1 else f"until you win {left} more fights"
        return f"for your next {unit}" if left == 1 else f"for your next {left} {unit}"
    return f"{left} {unit} left"


def announce_text(effect):
    """What praying (or the Prayer card) tells you: 'you got blessed: +15% rest odds for your next 3 rest attempts'"""
    if effect["kind"] == "Curse":
        return f"You got cursed! {change_text(effect)[0].upper()}{change_text(effect)[1:]} {lasts_text(effect, True)}."
    return f"You got blessed! You now have {change_text(effect)} {lasts_text(effect, True)}."


def describe(effect):
    """For View Stats: 'Of fear (Curse): Charisma -999, 5 explores left'"""
    return f"{effect['name']} ({effect['kind']}): {change_text(effect)}, {lasts_text(effect)}"
