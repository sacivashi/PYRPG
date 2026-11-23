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


def describe(effect):
    """'Of fear (Curse): Charisma -999, 5 explores left'"""
    op, value = effect["op"], _whole(effect["value"])
    change = {"+": f"+{value}", "-": f"-{value}", "*": f"x{value}"}[op]
    if effect["ticks_on"] == UNTIL_RESTED:
        lasts = "until you rest"
    else:
        unit = {"rest": "rest attempt", "rested": "successful rest", "victory": "win",
                "explore": "explore"}[effect["ticks_on"][0]]
        lasts = f"{effect['left']} {unit}{'s' if effect['left'] != 1 else ''} left"
    return f"{effect['name']} ({effect['kind']}): {effect['target']} {change}, {lasts}"
