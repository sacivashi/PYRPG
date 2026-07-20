import random


class Player:
    # Player class for combat — handles live HP, damage, healing during a fight
    def __init__(self, name, role, level, stats):
        self.name = name
        self.role = role
        self.level = level
        self.stats = stats
        self.current_hp = self.calculate_hp()
        self.max_hp = self.current_hp

    @classmethod
    def extract_player(cls, player_data):
        if isinstance(player_data, dict):  # Existing player from CSV
            return cls(player_data["name"], player_data["role"], player_data["level"], player_data["stats"])
        name, role, level, hp, stats = player_data  # New player tuple — hp recalculated from stats
        return cls(name, role, level, stats)

    def calculate_hp(self):
        return abs((int(self.stats['Strength']) + int(self.stats['Defence'])) / 0.2)

    def player_data(self):
        return (self.name, self.role, self.level, self.current_hp, self.stats)

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
