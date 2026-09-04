import random

from players.player_data import PlayerData
from items.items_data import get_item_stats, STAT_COLUMNS


class Player:
    # Player class for combat — handles live HP, damage, healing during a fight
    def __init__(self, player_data, role=None, level=None, stats=None, hp=None):
        if isinstance(player_data, PlayerData):
            self.name = player_data.name
            self.role = player_data.role
            self.level = player_data.level
            self.base_stats = dict(player_data.stats)  # copy — combat mutations must not leak into the caller's PlayerData
            self.equipped = player_data.equipped
            self.stats = self.apply_equipment(self.base_stats, self.equipped)
            self.max_hp = self.calculate_hp(self.stats)
            self.current_hp = self._resolve_current_hp(player_data.hp, player_data.max_hp, self.max_hp)
            self.gold = player_data.gold
            self.loot = list(player_data.loot)
            return

        if isinstance(player_data, tuple):
            name, role, level, hp, stats = player_data
            player_data = PlayerData(name=name, role=role, level=level, hp=hp, stats=stats)
            self.name = player_data.name
            self.role = player_data.role
            self.level = player_data.level
            self.base_stats = dict(player_data.stats)
            self.equipped = player_data.equipped
            self.stats = self.apply_equipment(self.base_stats, self.equipped)
            self.max_hp = self.calculate_hp(self.stats)
            self.current_hp = self._resolve_current_hp(player_data.hp, player_data.max_hp, self.max_hp)
            self.gold = player_data.gold
            self.loot = list(player_data.loot)
            return

        self.name = player_data
        self.role = role
        self.level = level if level is not None else 1
        self.base_stats = dict(stats) if stats else {}
        self.equipped = None
        self.stats = self.apply_equipment(self.base_stats, self.equipped)
        self.max_hp = self.calculate_hp(self.stats)
        self.current_hp = min(hp if hp is not None else self.max_hp, self.max_hp)
        self.gold = 0
        self.loot = []

    @staticmethod
    def extract_player(player_data):
        return Player(player_data)

    @staticmethod
    def apply_equipment(base_stats, equipped_name):
        """Merge the equipped item's stat deltas onto a copy of base_stats. Base stats
        (and what gets saved) are never mutated — only this derived copy reflects gear."""
        effective_stats = dict(base_stats)
        if not equipped_name:
            return effective_stats

        if equipped_name.lower() == "dice machine":
            # Rerolls fresh every equip instead of a fixed stat block from the CSV
            item_deltas = {stat: random.randint(-5, 5) for stat in STAT_COLUMNS}
        else:
            item_deltas = get_item_stats(equipped_name)

        if item_deltas:
            for stat, delta in item_deltas.items():
                effective_stats[stat] = effective_stats.get(stat, 0) + delta
        return effective_stats

    @staticmethod
    def calculate_hp(stats):
        # max(22, abs(Strength) * 0.95 + abs(Defence) * 2.3)
        return int(max(22, abs(int(stats['Strength'])) * 0.95 + abs(int(stats['Defence'])) * 2.3))

    @staticmethod
    def _resolve_current_hp(saved_hp, saved_max_hp, new_max_hp):
        """Preserve damage taken across max_hp changes (formula tweaks, stat changes) by
        healing the difference when max_hp increases, instead of leaving HP stranded below the new cap."""
        hp_gain = max(0, new_max_hp - (saved_max_hp if saved_max_hp is not None else new_max_hp))
        return min(new_max_hp, saved_hp + hp_gain)

    def player_data(self):
        return PlayerData(self.name, self.role, self.level, self.current_hp, self.base_stats,
                           max_hp=self.max_hp, gold=self.gold, loot=self.loot, equipped=self.equipped)

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
        self.current_hp = max(0, round(self.current_hp - damage))
        return self.current_hp <= 0  # Returns True if player is defeated

    def heal(self, amount):
        self.current_hp = min(self.max_hp, round(self.current_hp + amount))

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
