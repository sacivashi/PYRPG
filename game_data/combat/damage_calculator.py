import random
import math

class DamageCalculator:
    """Damage calculation system implementing exact patch notes Alpha II negative stat effects"""
    
    @staticmethod
    def calculate_base_damage(attacker_stats, weapon_bonus=0):
        """Calculate base damage from attacker's stats"""
        stats = {k: int(v) for k, v in attacker_stats.items()}
        
        # Get primary offensive stats (excluding Defence)
        offensive_stats = {k: v for k, v in stats.items() if k not in ['Defence', 'HP']}
        
        if not offensive_stats:
            return 0
            
        # Use highest offensive stat as base
        base_damage = max(offensive_stats.values())
        
        # Add weapon bonus
        base_damage += weapon_bonus
        
        return max(0, base_damage)
    
    @staticmethod
    def apply_strength_modifier(base_damage, strength, player_max_hp=None):
        """Apply strength-based modifications from patch notes"""
        if strength < 0:
            # From patch notes: -Strength
            # Debuff: Missing attacks makes you hit yourself for (HP -(-x) * 2) damage
            # Benefit: hitting enemies heals you by (max HP / (X + n))
            miss_chance = abs(strength) * 0.15  # Higher miss chance for negative strength
            if random.random() < miss_chance:
                if player_max_hp:
                    # Self-damage: (HP - (-x) * 2) = (max_hp - abs(strength) * 2)
                    self_damage = abs(player_max_hp - (abs(strength) * 2))
                else:
                    self_damage = abs(strength) * 3  # Fallback
                return 0, ("self_damage", self_damage)
            else:
                # Benefit: Healing when hitting
                if player_max_hp:
                    heal_amount = player_max_hp / (abs(strength) + 1)  # max HP / (X + n)
                else:
                    heal_amount = 5  # Fallback
                return base_damage, ("heal_on_hit", heal_amount)
        else:
            # Normal strength bonus
            strength_multiplier = 1 + (strength * 0.15)
            return base_damage * strength_multiplier, None
    
    @staticmethod
    def apply_agility_modifier(initiative_bonus, agility):
        """Apply agility-based modifications from patch notes"""
        if agility < 0:
            # From patch notes: -Agility  
            # Debuff: Always act last (-speed enemies not included)
            # Benefit: Incoming attacks are easier to read — +X% dodge or counter chance
            dodge_counter_chance = abs(agility) * 0.1  # +X% dodge/counter
            return -1000, dodge_counter_chance  # Always go last, but gain dodge/counter
        else:
            # Normal agility bonus to initiative
            return agility + random.randint(0, 5), 0
    
    @staticmethod
    def apply_intelligence_modifier(damage, intelligence, attacker_stats):
        """Apply intelligence-based modifications from patch notes"""
        if intelligence < 0:
            # From patch notes: -Intelligence
            # Debuff: (100 / X + RNG)% to attack a different enemy
            # Benefit: you hit harder (N * X - (INT of: highest stat / 10))
            confusion_chance = (100 / abs(intelligence)) + random.randint(1, 10)
            if random.random() < (confusion_chance / 100):
                return 0, "confused"  # Attack wrong target
            else:
                # Benefit: Hit harder calculation
                highest_stat = max([v for k, v in attacker_stats.items() if k not in ['Intelligence', 'Defence', 'HP']])
                bonus_damage = (damage * abs(intelligence)) - (highest_stat / 10)
                return damage + bonus_damage, "focused"
        else:
            # Normal intelligence bonus
            int_bonus = intelligence * 0.2
            return damage + int_bonus, "normal"
    
    @staticmethod
    def apply_defence_modifier(incoming_damage, defence):
        """Apply defence-based modifications from patch notes"""
        if defence < 0:
            # From patch notes: -Defence
            # Debuff: Getting hit makes you take (-X) damage bonus  
            # Benefit: you damage the attacker by (damage / 75 + X) back
            extra_damage = abs(defence)  # Take extra damage
            final_damage = incoming_damage + extra_damage
            
            # Reflect damage back: (damage / 75 + X)
            reflected_damage = (incoming_damage / 75) + abs(defence)
            return final_damage, ("reflect_damage", reflected_damage)
        else:
            # Normal defence: reduce incoming damage
            damage_reduction = defence * 0.1  # 10% reduction per defence point
            final_damage = incoming_damage * (1 - min(0.8, damage_reduction))  # Cap at 80%
            return final_damage, None
    
    @staticmethod
    def apply_luck_modifier(damage, luck_stat):
        """Apply luck-based modifications from patch notes"""
        if luck_stat < 0:
            # From patch notes: -Luck
            # Debuff: higher chance to miss attacks, lower loot rolls
            # Benefit: Successful attacks are unavoidable
            miss_chance = abs(luck_stat) * 0.12  # Higher miss chance
            if random.random() < miss_chance:
                return 0, False  # Missed attack
            else:
                # Benefit: Unavoidable when it hits
                return damage, True  # True = unavoidable
        else:
            # Positive luck: Random bonus
            luck_roll = random.randint(0, 5)
            luck_bonus = luck_roll * (luck_stat / 10)
            return damage + luck_bonus, False
    
    @staticmethod
    def apply_magic_modifier(damage, magic_stat, is_magic_attack=False):
        """Apply magic-based modifications from patch notes"""
        if magic_stat < 0 and is_magic_attack:
            # From patch notes: -Magic
            # Debuff: using cursed magika makes you suffer (X + n) self damage
            # Benefit: you have a chance to lower the enemy stats
            self_damage = abs(magic_stat) + random.randint(1, 3)  # X + n
            stat_debuff_chance = abs(magic_stat) * 0.15
            
            effects = [("self_damage", self_damage)]
            if random.random() < stat_debuff_chance:
                effects.append(("enemy_stat_debuff", abs(magic_stat)))
            
            return damage, effects
        elif magic_stat > 0 and is_magic_attack:
            # Normal magic bonus for magical attacks
            magic_bonus = magic_stat * 0.25
            return damage + magic_bonus, []
        else:
            return damage, []
    
    @staticmethod
    def calculate_player_damage(player_stats, player_max_hp, is_magic_attack=False, weapon_bonus=0):
        """Calculate total player damage with all negative stat effects"""
        stats = {k: int(v) for k, v in player_stats.items()}
        
        # Base damage
        base_damage = DamageCalculator.calculate_base_damage(stats, weapon_bonus)
        
        special_effects = []
        final_damage = base_damage
        is_unavoidable = False
        
        # Apply Strength modifier
        final_damage, strength_effect = DamageCalculator.apply_strength_modifier(
            final_damage, stats.get('Strength', 0), player_max_hp
        )
        if strength_effect:
            special_effects.append(strength_effect)
            if strength_effect[0] == "self_damage":
                return 0, special_effects, False  # Attack failed due to self-damage
        
        # Apply Intelligence modifier  
        final_damage, intel_effect = DamageCalculator.apply_intelligence_modifier(
            final_damage, stats.get('Intelligence', 0), stats
        )
        if intel_effect == "confused":
            return 0, [("confusion", True)], False
        elif intel_effect == "focused":
            special_effects.append(("focused_attack", True))
        
        # Apply Luck modifier
        final_damage, unavoidable = DamageCalculator.apply_luck_modifier(
            final_damage, stats.get('Luck', 0)
        )
        is_unavoidable = unavoidable
        
        # Apply Magic modifier if it's a magic attack
        final_damage, magic_effects = DamageCalculator.apply_magic_modifier(
            final_damage, stats.get('Magic', 0), is_magic_attack
        )
        special_effects.extend(magic_effects)
        
        return round(max(0, final_damage), 2), special_effects, is_unavoidable
    
    @staticmethod
    def calculate_damage_taken(incoming_damage, defender_stats, defender_agility_bonus=0):
        """Calculate damage taken by defender with negative stat effects"""
        stats = {k: int(v) for k, v in defender_stats.items()}
        
        counter_effects = []
        final_damage = incoming_damage
        
        # Apply Defence modifier
        final_damage, defence_effect = DamageCalculator.apply_defence_modifier(
            final_damage, stats.get('Defence', 0)
        )
        if defence_effect:
            counter_effects.append(defence_effect)
        
        # Apply Agility dodge/counter from negative agility bonus
        if defender_agility_bonus > 0:  # This is the dodge/counter chance from negative agility
            if random.random() < defender_agility_bonus:
                action = random.choice(["dodge", "counter"])
                if action == "dodge":
                    return 0, [("dodged", True)]
                else:
                    counter_effects.append(("counter_attack", True))
        elif stats.get('Agility', 0) > 0:
            # Normal dodge chance for positive agility
            dodge_chance = min(0.25, stats.get('Agility', 0) * 0.04)
            if random.random() < dodge_chance:
                return 0, [("dodged", True)]
        
        return round(max(0, final_damage), 2), counter_effects

    @staticmethod
    def calculate_enemy_damage(enemy_stats, enemy_name):
        """Calculate enemy damage with negative stat effects"""
        stats = {k: int(v) for k, v in enemy_stats.items()}
        
        # Enemy negative stat effects from patch notes:
        strength = stats.get('Strength', 5)
        luck = stats.get('Luck', 0)
        
        if strength < 0:
            # -Attack: The enemy deals 0 damage, but will heal itself based on the -X amount when hit
            return 0, [("enemy_heals_when_hit", abs(strength))]
        
        base_damage = max(1, strength)
        
        if luck < 0:
            # -Luck: higher missing% on attacks, successful hits curse a player's stat
            miss_chance = abs(luck) * 0.15
            if random.random() < miss_chance:
                return 0, []  # Enemy misses
            else:
                # Successful hit curses player stat
                curse_amount = abs(luck)
                return base_damage, [("curse_player_stat", curse_amount)]
        
        # Normal enemy damage with some variance
        variance = random.randint(-2, 3)
        return max(1, base_damage + variance), []