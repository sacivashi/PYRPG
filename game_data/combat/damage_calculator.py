import random
import math


class DamageCalculator:
    """Damage calculation system — Alpha II patch notes formulas"""

    @staticmethod
    def calculate_base_damage(attacker_stats, weapon_bonus=0):
        stats = {k: int(v) for k, v in attacker_stats.items()}
        offensive_stats = {k: v for k, v in stats.items() if k not in ['Defence', 'HP']}
        if not offensive_stats:
            return 0
        base_damage = max(offensive_stats.values())
        base_damage += weapon_bonus
        return max(0, base_damage)

    @staticmethod
    def apply_strength_modifier(base_damage, strength):
        if strength < 0:
            # Debuff: take abs(-str) after every attack
            # Benefit: heal on hit — formula computed in combat.py using final_damage
            #   int(sqrt(missing_hp + damage_done) + abs(-str * 1.5))
            self_damage = abs(strength)
            return base_damage, [("self_damage_after_hit", self_damage), ("heal_on_hit", abs(strength))]
        else:
            strength_multiplier = 1 + (strength * 0.15)
            return base_damage * strength_multiplier, []

    @staticmethod
    def apply_agility_modifier(initiative_bonus, agility):
        if agility < 0:
            # Debuff: always act last
            # Benefit: +min(35, abs(-agi))% dodge rate
            dodge_chance = min(35, abs(agility)) / 100
            return -1000, dodge_chance
        else:
            return agility + random.randint(0, 5), 0

    @staticmethod
    def apply_intelligence_modifier(damage, intelligence, attacker_stats):
        if intelligence < 0:
            # Debuff: min(50, abs(-int) + 5)% confusion chance
            confusion_chance = min(50, abs(intelligence) + 5) / 100
            if random.random() < confusion_chance:
                return 0, "confused"
            else:
                # Benefit: +2*abs(-int) - (highest_stat / 10) flat bonus damage
                highest_stat = max([v for k, v in attacker_stats.items() if k not in ['Intelligence', 'Defence', 'HP']])
                bonus_damage = 2 * abs(intelligence) - (highest_stat / 10)
                return damage + max(0, bonus_damage), "focused"
        else:
            int_bonus = intelligence * 0.2
            return damage + int_bonus, "normal"

    @staticmethod
    def apply_defence_modifier(incoming_damage, defence, is_enemy=False):
        if defence < 0:
            extra_damage = abs(defence)
            final_damage = incoming_damage + extra_damage
            if is_enemy:
                # Enemy -Defence: reflect (damage / 100 + abs(-def))
                reflected_damage = (incoming_damage / 100) + abs(defence)
            else:
                # Player -Defence: reflect int((damage * 1.5 + abs(-def)) / 2.5)
                reflected_damage = int((incoming_damage * 1.5 + abs(defence)) / 2.5)
            return final_damage, ("reflect_damage", reflected_damage)
        else:
            damage_reduction = defence * 0.1
            final_damage = incoming_damage * (1 - min(0.8, damage_reduction))
            return final_damage, None

    @staticmethod
    def apply_luck_modifier(damage, luck_stat):
        if luck_stat < 0:
            # Debuff: min(35, abs(-lck))% miss chance
            # Benefit: successful attacks are unavoidable
            miss_chance = min(35, abs(luck_stat)) / 100
            if random.random() < miss_chance:
                return 0, False
            else:
                return damage, True  # unavoidable
        else:
            luck_roll = random.randint(0, 5)
            luck_bonus = luck_roll * (luck_stat / 10)
            return damage + luck_bonus, False

    @staticmethod
    def apply_magic_modifier(damage, magic_stat, is_magic_attack=False, player_max_hp=None):
        if magic_stat < 0 and is_magic_attack:
            # Debuff: drain abs(-mag)% of MAX HP
            drain = math.ceil(abs(magic_stat) / 100 * player_max_hp) if player_max_hp else abs(magic_stat)
            # Benefit: min(65, int(sqrt(abs(-mag)) * 10))% chance to debuff enemy stat
            debuff_chance = min(65, int(math.sqrt(abs(magic_stat)) * 10)) / 100
            effects = [("hp_drain", drain)]
            if random.random() < debuff_chance:
                effects.append(("enemy_stat_debuff", abs(magic_stat)))
            return damage, effects
        elif magic_stat > 0 and is_magic_attack:
            magic_bonus = magic_stat * 0.25
            return damage + magic_bonus, []
        else:
            return damage, []

    @staticmethod
    def calculate_player_damage(player_stats, player_max_hp, player_current_hp, is_magic_attack=False, weapon_bonus=0):
        stats = {k: int(v) for k, v in player_stats.items()}
        base_damage = DamageCalculator.calculate_base_damage(stats, weapon_bonus)

        special_effects = []
        final_damage = base_damage
        is_unavoidable = False

        # Strength
        final_damage, strength_effects = DamageCalculator.apply_strength_modifier(
            final_damage, stats.get('Strength', 0)
        )
        special_effects.extend(strength_effects)

        # Intelligence
        final_damage, intel_effect = DamageCalculator.apply_intelligence_modifier(
            final_damage, stats.get('Intelligence', 0), stats
        )
        if intel_effect == "confused":
            return 0, [("confusion", True)], False
        elif intel_effect == "focused":
            special_effects.append(("focused_attack", True))

        # Luck
        final_damage, unavoidable = DamageCalculator.apply_luck_modifier(
            final_damage, stats.get('Luck', 0)
        )
        if final_damage == 0 and not unavoidable:
            return 0, special_effects, False  # missed
        is_unavoidable = unavoidable

        # Magic
        final_damage, magic_effects = DamageCalculator.apply_magic_modifier(
            final_damage, stats.get('Magic', 0), is_magic_attack, player_max_hp
        )
        special_effects.extend(magic_effects)

        return round(max(0, final_damage), 2), special_effects, is_unavoidable

    @staticmethod
    def calculate_damage_taken(incoming_damage, defender_stats, defender_agility_bonus=0, is_enemy=False):
        stats = {k: int(v) for k, v in defender_stats.items()}
        counter_effects = []
        final_damage = incoming_damage

        # Defence
        final_damage, defence_effect = DamageCalculator.apply_defence_modifier(
            final_damage, stats.get('Defence', 0), is_enemy
        )
        if defence_effect:
            counter_effects.append(defence_effect)

        # Agility dodge/counter
        if defender_agility_bonus > 0:
            if random.random() < defender_agility_bonus:
                action = random.choice(["dodge", "counter"])
                if action == "dodge":
                    return 0, [("dodged", True)]
                else:
                    counter_effects.append(("counter_attack", True))
        elif stats.get('Agility', 0) > 0:
            dodge_chance = min(0.25, stats.get('Agility', 0) * 0.04)
            if random.random() < dodge_chance:
                return 0, [("dodged", True)]

        return round(max(0, final_damage), 2), counter_effects

    @staticmethod
    def calculate_enemy_damage(enemy_stats, enemy_name):
        stats = {k: int(v) for k, v in enemy_stats.items()}

        strength = stats.get('Strength', 5)
        luck = stats.get('Luck', 0)

        if strength < 0:
            # -Attack: deals 0 damage, heals when hit
            return 0, [("enemy_heals_when_hit", abs(strength))]

        base_damage = max(1, strength)

        if luck < 0:
            # -Luck: min(45, abs(-lck) * 1.5)% miss chance, curse on hit
            miss_chance = min(45, abs(luck) * 1.5) / 100
            if random.random() < miss_chance:
                return 0, []
            else:
                return base_damage, [("curse_player_stat", abs(luck))]

        variance = random.randint(-2, 3)
        return max(1, base_damage + variance), []
