import random


class Player:
    """Unified player class for both new and existing players"""
    def __init__(self, player_data):
        if isinstance(player_data, dict):  # Existing player from CSV
            self.name = player_data["name"]
            self.role = player_data["role"]
            self.level = player_data["level"]
            self.stats = player_data["stats"]
            self.current_hp = self.calculate_hp()
            self.max_hp = self.current_hp
        else:  # New player tuple
            name, role, level, hp, stats = player_data
            self.name = name
            self.role = role
            self.level = level
            self.stats = stats
            self.current_hp = hp
            self.max_hp = hp

    def calculate_hp(self):
        """Calculate HP based on stats"""
        return abs((int(self.stats['Strength']) + int(self.stats['Defence'])) / 0.2)

    def get_live_stats(self):
        """Get current live stats for combat calculations"""
        return {
            'name': self.name,
            'role': self.role,
            'level': self.level,
            'current_hp': self.current_hp,
            'max_hp': self.max_hp,
            'stats': {k: int(v) for k, v in self.stats.items()}
        }

    def take_damage(self, damage):
        """Apply damage to player"""
        self.current_hp = max(0, self.current_hp - damage)
        return self.current_hp <= 0  # Returns True if player is defeated

    def heal(self, amount):
        """Heal player"""
        self.current_hp = min(self.max_hp, self.current_hp + amount)

    def is_alive(self):
        return self.current_hp > 0

    def calculate_damage(self, str_percent=0.5, luck_range=(0, 5)):
        # Convert stat strings to integers
        stats = {k: int(v) for k, v in self.stats.items()}

        # Get the highest offensive stat (excluding Defence)
        offensive_stats = {k: v for k, v in stats.items() if k != 'Defence'}
        highest_stat_value = max(offensive_stats.values())

        # Strength bonus
        strength_bonus = stats.get('Strength', 0) * str_percent

        # Luck bonus
        luck_stat = stats.get('Luck', 0)
        luck_random_roll = random.randint(*luck_range)
        luck_bonus = luck_random_roll * (luck_stat / 10)

        # Final damage value
        total_damage = highest_stat_value + strength_bonus + luck_bonus
        return round(total_damage, 2)
