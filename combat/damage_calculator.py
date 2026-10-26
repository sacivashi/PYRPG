import random
import math


class DamageCalculator:
    """Damage calculation system — v1.0 patch notes formulas (physical/magic split)"""

    PHYSICAL_STATS = ['Strength', 'Agility', 'Luck', 'Defence']

    # No source of evasion can push a dodge chance past this. Anything that adds evasion later
    # (e.g. gear) should be summed into calculate_evasion_chance so this cap covers it too.
    EVASION_CAP = 0.35

    @staticmethod
    def calculate_evasion_chance(agility):
        """Dodge chance from positive Agility: 4% per point, capped at EVASION_CAP"""
        return min(DamageCalculator.EVASION_CAP, max(0, agility) * 0.04)

    @staticmethod
    def calculate_flee_chance(agility, enemy_speed):
        """Continuous through 25% at Agility 0: max(20, 25 - abs(agi)*0.25)% for -Agility,
        min(60, 25 + agi*2)% for +Agility. A -Speed enemy adds +min(15, abs(-spd)*0.3)% on top,
        since a slower enemy is easier to outrun."""
        if agility < 0:
            base = max(20, 25 - abs(agility) * 0.25)
        else:
            base = min(60, 25 + agility * 2)

        if enemy_speed < 0:
            base += min(15, abs(enemy_speed) * 0.3)

        return round(min(100, base), 1)

    # --- Physical attacks -------------------------------------------------------------------

    @staticmethod
    def calculate_base_damage(attacker_stats, weapon_bonus=0):
        """v1.0 physical damage: int(sqrt(abs(Str) + abs(Agi) + abs(Lck) + abs(Def) + 15) * 2.2).
        Every physical stat counts (Defence too — you can hit with your shield), each by its size,
        so a negative stat adds as much as a positive one. The square root keeps high-stat roles
        from running away with it; the +15 gives everyone a floor of 8."""
        stats = {k: int(v) for k, v in attacker_stats.items()}
        total = sum(abs(stats.get(stat, 0)) for stat in DamageCalculator.PHYSICAL_STATS)
        return max(0, int(math.sqrt(total + 15) * 2.2) + weapon_bonus)

    @staticmethod
    def strength_self_damage(strength, max_hp):
        """-Strength debuff: physical attacks and abilities sear you for
        int(abs(str) + int(min(max_hp * 0.08, abs(str)) * 0.5)), hit or miss"""
        if strength >= 0:
            return 0
        return int(abs(strength) + int(min(max_hp * 0.08, abs(strength)) * 0.5))

    @staticmethod
    def strength_heal(strength, missing_hp, damage_done):
        """-Strength benefit: landing a physical attack or ability heals
        min((abs(str) + missing_hp) * 0.8, (damage_done + abs(str)) * 0.65)"""
        if strength >= 0:
            return 0
        return int(min((abs(strength) + missing_hp) * 0.8, (damage_done + abs(strength)) * 0.65))

    @staticmethod
    def apply_agility_modifier(agility):
        if agility < 0:
            # Debuff: acts last unless opponent's agility/speed is lower (raw value used for initiative comparison)
            # Benefit: +min(15, max(5, abs(-agi)))% evasion
            dodge_chance = min(15, max(5, abs(agility))) / 100
            return agility, dodge_chance
        else:
            return agility + random.randint(0, 5), 0

    # Single-target ability damage (v1.0 "other spells & abilities"). Damage type lives in SPELLS.
    ABILITY_FORMULAS = {
        "Arrowshot": lambda s: int(s.get('Agility', 0) * 0.7 + abs(s.get('Magic', 0)) * 0.3),
        "Backstab": lambda s: int(15 + s.get('Agility', 0) * 0.8),
        "Blade bonk": lambda s: int(5 + s.get('Strength', 0) * 0.55),
        "Shield bash": lambda s: int(s.get('Defence', 0) * 1.5),
    }

    @staticmethod
    def ability_damage(name, attacker_stats):
        stats = {k: int(v) for k, v in attacker_stats.items()}
        return max(0, DamageCalculator.ABILITY_FORMULAS[name](stats))

    @staticmethod
    def berserk_bonus(strength):
        """Berserk scream: physical attacks deal +int(max(1, str * 0.45)) until combat ends"""
        return int(max(1, strength * 0.45))

    @staticmethod
    def defend_block(defence):
        """Defending: on top of the usual Defence %, block a flat min(10, max(0, def * 0.75))"""
        return min(10, max(0, defence * 0.75))

    @staticmethod
    def apply_luck_modifier(damage, luck_stat):
        """-Luck: min(35, abs(-lck))% miss chance, but hits that land are unavoidable.
        (+Luck no longer adds a random bonus — it counts through calculate_base_damage instead.)"""
        if luck_stat < 0:
            miss_chance = min(35, abs(luck_stat)) / 100
            if random.random() < miss_chance:
                return 0, False
            return damage, True  # unavoidable
        return damage, False

    @staticmethod
    def calculate_player_damage(player_stats, weapon_bonus=0):
        """Physical attack: (damage, unavoidable). Damage 0 means the attack missed (-Luck)."""
        stats = {k: int(v) for k, v in player_stats.items()}
        damage = DamageCalculator.calculate_base_damage(stats, weapon_bonus)
        damage, unavoidable = DamageCalculator.apply_luck_modifier(damage, stats.get('Luck', 0))
        return max(0, damage), unavoidable

    # --- Spells -----------------------------------------------------------------------------

    @staticmethod
    def spell_multiplier(magic, cursed=False):
        """Normal spells: max(0.1, 1 + Magic * 0.1). Cursed spells: max(0.1, 1 + abs(Magic) * 0.1)."""
        scaling = abs(magic) if cursed else magic
        return max(0.1, 1 + scaling * 0.1)

    @staticmethod
    def intelligence_spell_bonus(spell_damage, intelligence, magic):
        """-Intelligence benefit (spells only): int(0.5 * spell_damage) + int(min(abs(int) // 3, abs(mag) * 0.8))"""
        if intelligence >= 0:
            return 0
        return int(0.5 * spell_damage) + int(min(abs(intelligence) // 3, abs(magic) * 0.8))

    @staticmethod
    def mana_waste_chance(intelligence):
        """-Intelligence debuff: min(35, abs(int) + 5)% chance a spell/ability costs 1.5x"""
        return min(35, abs(intelligence) + 5) if intelligence < 0 else 0

    @staticmethod
    def cursed_hp_cost(magic, cost):
        """-Magic: cursed spells cost min(abs(mag), cost * 0.88) HP instead of mana"""
        return min(abs(magic), cost * 0.88)

    @staticmethod
    def cursed_debuff_chance(magic):
        """-Magic benefit: min(65, int(sqrt(abs(mag)) * 10))% for a cursed spell to lower a random enemy stat"""
        return min(65, int(math.sqrt(abs(magic)) * 10)) if magic < 0 else 0

    @staticmethod
    def cursed_debuff_amount(magic):
        return min(7, abs(magic))

    # --- Hits landing on an enemy -------------------------------------------------------------

    @staticmethod
    def enemy_defence_adjustment(damage, defence, damage_type):
        """Enemy Defense vs a player hit. damage_type: 'physical' (attacks + abilities), 'spell', or
        'item' / 'searing' (unaffected). Returns (damage, reflected_back_to_player).
          +Def: physical takes min(20, 2 + def * 0.9)% less, spells min(15, 1 + def * 0.2)% less
          -Def: physical takes +max(3, abs(def) * 0.75) and reflects min(11, abs(def) * 0.4)% of
                the flat (pre-bonus) damage; spells take +max(7, abs(def) * 0.82), no reflect
          0 Def: no change"""
        if damage_type in ("item", "searing") or defence == 0:
            return damage, 0
        if defence > 0:
            if damage_type == "spell":
                reduction = min(15, 1 + defence * 0.2)
            else:
                reduction = min(20, 2 + defence * 0.9)
            return damage * (1 - reduction / 100), 0
        if damage_type == "spell":
            return damage + max(7, abs(defence) * 0.82), 0
        reflected = damage * min(11, abs(defence) * 0.4) / 100
        return damage + max(3, abs(defence) * 0.75), reflected

    @staticmethod
    def corruption_tick_damage(current_hp, corruption):
        """End of a corrupted enemy's turn: max(current_hp * 0.04, corr, 3) searing damage"""
        return max(current_hp * 0.04, corruption, 3)

    @staticmethod
    def corruption_hit(damage, corruption):
        """A hit on a corrupted enemy is reduced by corr. Returns (damage_dealt, heal): a hit that
        doesn't clear corr deals nothing and heals the enemy for min(corr * 0.75, abs(damage - corr))."""
        reduced = damage - corruption
        if reduced > 0:
            return reduced, 0
        return 0, min(corruption * 0.75, abs(reduced))

    # --- Hits landing on the player -----------------------------------------------------------

    @staticmethod
    def player_damage_reduction(defence):
        """+Defence: take min(25, 2 + def * 0.7)% less damage. 0 or -Defence: no reduction."""
        return min(25, 2 + defence * 0.7) / 100 if defence > 0 else 0

    @staticmethod
    def apply_defence_modifier(incoming_damage, defence, is_enemy=False, max_hp=0):
        if defence < 0:
            if is_enemy:
                final_damage, reflected = DamageCalculator.enemy_defence_adjustment(incoming_damage, defence, "physical")
                return final_damage, ("reflect_damage", reflected)
            # Player -Defence: max(max_hp * 0.05, abs(-def)) bonus damage taken
            extra_damage = max(max_hp * 0.05, abs(defence))
            # Player -Defence: reflect max(15, min(35, max(damage_taken, abs(-def)) * 0.35))% of flat damage (pre-bonus)
            reflect_percent = max(15, min(35, max(incoming_damage, abs(defence)) * 0.35)) / 100
            return incoming_damage + extra_damage, ("reflect_damage", incoming_damage * reflect_percent)
        if is_enemy:
            return DamageCalculator.enemy_defence_adjustment(incoming_damage, defence, "physical")[0], None
        return incoming_damage * (1 - DamageCalculator.player_damage_reduction(defence)), None

    @staticmethod
    def calculate_damage_taken(incoming_damage, defender_stats, defender_agility_bonus=0, is_enemy=False, unavoidable=False, max_hp=0):
        stats = {k: int(v) for k, v in defender_stats.items() if k != "Name"}
        counter_effects = []
        final_damage = incoming_damage

        # Defence (enemies use 'Defense', players use 'Defence')
        defence_key = 'Defense' if is_enemy else 'Defence'
        final_damage, defence_effect = DamageCalculator.apply_defence_modifier(
            final_damage, stats.get(defence_key, 0), is_enemy, max_hp
        )
        if defence_effect:
            counter_effects.append(defence_effect)

        # Agility dodge/counter — skipped entirely for unavoidable attacks
        if not unavoidable:
            dodged, countered = DamageCalculator.roll_dodge(defender_agility_bonus, stats.get('Agility', 0))
            if dodged:
                return 0, [("dodged", True)]
            if countered:
                counter_effects.append(("counter_attack", True))

        return round(max(0, final_damage), 2), counter_effects

    @staticmethod
    def roll_dodge(dodge_bonus, agility=0):
        """(dodged, countered). A -Agility/-Speed dodge bonus splits evenly into dodge or counter;
        otherwise positive Agility gives a plain dodge chance."""
        if dodge_bonus > 0:
            if random.random() < dodge_bonus:
                return (True, False) if random.choice(["dodge", "counter"]) == "dodge" else (False, True)
        elif agility > 0:
            if random.random() < DamageCalculator.calculate_evasion_chance(agility):
                return True, False
        return False, False

    @staticmethod
    def calculate_enemy_damage(enemy_stats, enemy_name):
        stats = {k: int(v) for k, v in enemy_stats.items() if k != "Name"}

        attack = stats.get('Attack', 5)
        luck = stats.get('Luck', 0)
        speed = stats.get('Speed', 0)
        unavoidable = speed < 0  # -Speed: attacks cannot be avoided

        if attack < 0:
            # -Attack: max(0, 15 + (-att)) damage; always siphons max(5, abs(-atk) * 0.46) flat HP
            base_damage = max(0, 15 + attack)
            if luck < 0:
                miss_chance = min(45, abs(luck) * 1.5) / 100
                if random.random() < miss_chance:
                    return 0, []
            leech_amount = round(max(5, abs(attack) * 0.46), 1)
            effects = [("leech_on_hit", leech_amount)]
            if luck < 0:
                effects.append(("curse_player_stat", min(4, abs(luck))))
            if base_damage > 0 and unavoidable:
                effects.append(("unavoidable", True))
            return base_damage, effects

        base_damage = max(1, attack)

        if luck < 0:
            # -Luck: min(45, abs(-lck) * 1.5)% miss chance, curse on hit (capped at min(4, abs(-lck)))
            miss_chance = min(45, abs(luck) * 1.5) / 100
            if random.random() < miss_chance:
                return 0, []
            effects = [("curse_player_stat", min(4, abs(luck)))]
            if unavoidable:
                effects.append(("unavoidable", True))
            return base_damage, effects

        variance = random.randint(-2, 3)
        effects = [("unavoidable", True)] if unavoidable else []
        return max(1, base_damage + variance), effects
