import random


class Player:
    # Player class for combat — handles live HP, damage, healing during a fight
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
        return abs((int(self.stats['Strength']) + int(self.stats['Defence'])) / 0.2)

    def get_live_stats(self):
        return {
            'name': self.name,
            'role': self.role,
            'level': self.level,
            'current_hp': self.current_hp,
            'max_hp': self.max_hp,
            'stats': {k: int(v) for k, v in self.stats.items()}
        }

    def take_damage(self, damage):
        self.current_hp = max(0, self.current_hp - damage)
        return self.current_hp <= 0  # Returns True if player is defeated

    def heal(self, amount):
        self.current_hp = min(self.max_hp, self.current_hp + amount)

    def is_alive(self):
        return self.current_hp > 0

    def calculate_damage(self, str_percent=0.5, luck_range=(0, 5)):
        stats = {k: int(v) for k, v in self.stats.items()}

        offensive_stats = {k: v for k, v in stats.items() if k != 'Defence'}
        highest_stat_value = max(offensive_stats.values())

        strength_bonus = stats.get('Strength', 0) * str_percent

        luck_stat = stats.get('Luck', 0)
        luck_random_roll = random.randint(*luck_range)
        luck_bonus = luck_random_roll * (luck_stat / 10)

        total_damage = highest_stat_value + strength_bonus + luck_bonus
        return round(total_damage, 2)
