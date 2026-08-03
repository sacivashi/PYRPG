import random
import math


class DamageCalculator:
    """Damage calculation system — Beta I patch notes formulas"""

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
    def apply_strength_modifier(base_damage, strength, max_hp):
        if strength < 0:
            # Debuff: take abs(-str) + int(max_hp * 0.01) after every attack
            # Benefit: heal on hit — formula computed in combat.py using final_damage
            #   min(int(sqrt(missing_hp + damage_done) * 0.5), int(self_damage * 0.75))
            self_damage = abs(strength) + int(max_hp * 0.01)
            return base_damage, [("self_damage_after_hit", self_damage), ("heal_on_hit", abs(strength))]
        else:
            strength_multiplier = 1 + (strength * 0.15)
            return base_damage * strength_multiplier, []

    @staticmethod
    def apply_agility_modifier(agility):
        if agility < 0:
            # Debuff: acts last unless opponent's agility/speed is lower (raw value used for initiative comparison)
            # Benefit: +min(15, max(5, abs(-agi)))% evasion
            dodge_chance = min(15, max(5, abs(agility))) / 100
            return agility, dodge_chance
        else:
            return agility + random.randint(0, 5), 0

    @staticmethod
    def apply_intelligence_modifier(damage, intelligence, attacker_stats):
        if intelligence < 0:
            # Debuff: min(35, abs(-int) + 5)% confusion chance
            confusion_chance = min(35, abs(intelligence) + 5) / 100
            if random.random() < confusion_chance:
                return 0, "confused"
            else:
                # Benefit: int(0.08 * damage) + int(min(abs(-int) * 0.75, highest_stat // 8)) bonus damage
                highest_stat = max([v for k, v in attacker_stats.items() if k not in ['Intelligence', 'Defence', 'HP']])
                bonus_damage = int(0.08 * damage) + int(min(abs(intelligence) * 0.75, max(highest_stat, 0) // 8))
                return damage + max(0, bonus_damage), "focused"
        else:
            int_bonus = intelligence * 0.2
            return damage + int_bonus, "normal"

    @staticmethod
    def apply_defence_modifier(incoming_damage, defence, is_enemy=False, max_hp=0):
        if defence < 0:
            if is_enemy:
                # Enemy -Defense: +max(3, abs(-def) * 0.75) bonus damage taken
                extra_damage = max(3, abs(defence) * 0.75)
                # Enemy -Defense: reflect min(5, (damage_taken + abs(-def)) * 0.2)% of flat damage (pre-bonus)
                reflect_percent = min(5, (incoming_damage + abs(defence)) * 0.2) / 100
            else:
                # Player -Defence: max(max_hp * 0.05, abs(-def)) bonus damage taken
                extra_damage = max(max_hp * 0.05, abs(defence))
                # Player -Defence: reflect max(15, min(35, max(damage_taken, abs(-def)) * 0.35))% of flat damage (pre-bonus)
                reflect_percent = max(15, min(35, max(incoming_damage, abs(defence)) * 0.35)) / 100
            final_damage = incoming_damage + extra_damage
            reflected_damage = incoming_damage * reflect_percent
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
            # Debuff: drain min(25, abs(-mag))% of MAX HP
            drain_percent = min(25, abs(magic_stat))
            drain = math.ceil(drain_percent / 100 * player_max_hp) if player_max_hp else drain_percent
            # Benefit: min(65, int(sqrt(abs(-mag)) * 10))% chance to lower a random enemy stat by min(7, abs(-mag))
            debuff_chance = min(65, int(math.sqrt(abs(magic_stat)) * 10)) / 100
            effects = [("hp_drain", drain)]
            if random.random() < debuff_chance:
                effects.append(("enemy_stat_debuff", min(7, abs(magic_stat))))
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
            final_damage, stats.get('Strength', 0), player_max_hp
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
        stats = {k: int(v) for k, v in enemy_stats.items() if k != "Name"}

        attack = stats.get('Attack', 5)
        luck = stats.get('Luck', 0)
        speed = stats.get('Speed', 0)
        unavoidable = speed < 0  # -Speed: attacks cannot be avoided

        if attack < 0:
            # -Attack: max(0, 15 + (-att)) damage; on a landed hit, leeches
            # min(15, abs(-atk) * 0.46)% of the attack value from the player and heals itself by the same amount
            base_damage = max(0, 15 + attack)
            if luck < 0:
                miss_chance = min(45, abs(luck) * 1.5) / 100
                if random.random() < miss_chance:
                    return 0, []
            leech_rate = min(15, abs(attack) * 0.46) / 100
            leech_amount = round(leech_rate * abs(attack), 1)
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
