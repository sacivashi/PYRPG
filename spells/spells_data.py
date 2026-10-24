# Spells, cursed spells and abilities (v1.0 patch notes, "magic reworked").
#
# kind:
#   "spell"   — normal spell, mana cost, damage scaled by max(0.1, 1 + Magic * 0.1)
#   "cursed"  — -Magic only, costs HP instead of mana, damage scaled by max(0.1, 1 + abs(Magic) * 0.1)
#   "ability" — anyone, mana cost, damage is its own formula (spell boosts don't apply)
# target: "single", "aoe" or "self"
# cost_step / damage_step: added once per earlier cast of the same spell this combat (Mana surge)
# cost "all": spends the caster's entire current mana (Hyper beam)
# once_per_combat: can only be cast once per fight
# channel_turns: the ability keeps firing automatically on that many of the caster's turns
#   (the cast turn included) and the caster can't take other actions meanwhile (Blade rush)
# heal_per_turn / heal_turns: a heal-over-time on the caster, first tick on the cast turn (Nature's gift)
SPELLS = {
    "Mana surge": {"kind": "spell", "target": "single", "cost": 5, "cost_step": 3,
                   "base_damage": 2, "damage_step": 2},
    "DOOM": {"kind": "cursed", "target": "single", "cost": 8, "base_damage": 10},
    "Cursed strike": {"kind": "cursed", "target": "single", "cost": 3, "base_damage": 3},
    "Hyper beam": {"kind": "spell", "target": "single", "cost": "all", "once_per_combat": True},
    "Blade rush": {"kind": "ability", "target": "aoe", "cost": 22, "channel_turns": 4},
    "Nature's gift": {"kind": "ability", "target": "self", "cost": 25, "heal_per_turn": 5, "heal_turns": 3},
}

# Consumable item -> the spell/ability it teaches. Using the item learns it and uses the item up.
LEARNING_ITEMS = {
    "mana surge book": "Mana surge",
    "scroll of doom": "DOOM",
    "nature's codex": "Nature's gift",
    "blade rush": "Blade rush",
}

# Equipment -> spell granted for as long as it's worn (never permanently learned).
EQUIPMENT_SPELLS = {
    "beam staff": "Hyper beam",
}

# Roles that start with a learning item already in their inventory.
STARTING_ITEMS = {
    "mage": ["Mana surge book"],
    "monk": ["Nature's codex"],
    "necromancer": ["Scroll of doom"],
}


# Role -> {level: [spells learned on reaching that level]}. Natural level-up learning — anything
# the character can't learn (e.g. a cursed spell while Magic isn't negative) is skipped, and
# picked up later if it becomes learnable.
LEVEL_UP_SPELLS = {
    "forsaken": {2: ["Cursed strike"]},
}


def level_up_spells(role, level):
    """Every spell a role should know by this level, lowest level first"""
    by_level = LEVEL_UP_SPELLS.get(role.lower(), {})
    return [spell for lvl in sorted(by_level) if lvl <= level for spell in by_level[lvl]]


def get_spell(name):
    return SPELLS.get(name)


def learning_item_spell(item_name):
    """The spell an item teaches, or None if it isn't a learning item"""
    return LEARNING_ITEMS.get(item_name.lower()) if item_name else None


def equipment_spell(item_name):
    """The spell an equipped item grants, or None"""
    return EQUIPMENT_SPELLS.get(item_name.lower()) if item_name else None


def can_learn(spell_name, magic):
    """Cursed spells are exclusive to -Magic; everything else can be learned by anyone"""
    spell = get_spell(spell_name)
    return spell is not None and (spell["kind"] != "cursed" or magic < 0)


def spell_cost(spell_name, casts_so_far=0, current_mana=0):
    """Mana (or, for cursed spells, the pre-HP-conversion) cost of the next cast"""
    spell = get_spell(spell_name)
    if spell["cost"] == "all":
        return current_mana
    return spell["cost"] + spell.get("cost_step", 0) * casts_so_far


def spell_base_damage(spell_name, casts_so_far=0, mana_spent=0):
    """Base damage before the Magic multiplier. Hyper beam scales with the mana poured into it."""
    if spell_name == "Hyper beam":
        return int(max(5, mana_spent * 0.40))
    spell = get_spell(spell_name)
    return spell.get("base_damage", 0) + spell.get("damage_step", 0) * casts_so_far


def blade_rush_damage(stats):
    """max(4, int(str * 0.8 + abs(mag) * 0.4)) physical damage to every enemy, every channel turn"""
    return max(4, int(stats.get('Strength', 0) * 0.8 + abs(stats.get('Magic', 0)) * 0.4))
