import copy
import random
from dataclasses import fields

from players.player_data import PlayerData
from items.items_data import get_item_stats, STAT_COLUMNS


class Player:
    # Player class for combat — handles live HP, damage, healing during a fight

    # PlayerData fields Player tracks under its own names/rules; every other field is carried through as-is
    DERIVED_FIELDS = {"hp", "mana", "max_hp", "stats"}

    def __init__(self, player_data, role=None, level=None, stats=None, hp=None):
        if isinstance(player_data, tuple):
            name, role, level, hp, stats = player_data
            player_data = PlayerData(name=name, role=role, level=level, hp=hp, stats=stats)
        elif not isinstance(player_data, PlayerData):  # bare name
            player_data = PlayerData(name=player_data, role=role, level=level if level is not None else 1,
                                     hp=hp, stats=stats or {})

        # copies — combat mutations must not leak into the caller's PlayerData
        for f in fields(PlayerData):
            if f.name not in self.DERIVED_FIELDS:
                setattr(self, f.name, copy.copy(getattr(player_data, f.name)))
        self.base_stats = dict(player_data.stats)
        self.stats = self.apply_equipment(self.base_stats, self.equipped)
        self.max_hp = self.calculate_hp(self.stats)
        self.current_hp = (self.max_hp if player_data.hp is None
                           else self._resolve_current_hp(player_data.hp, player_data.max_hp, self.max_hp))
        self.max_mana = self.calculate_mana(self.stats)
        self.current_mana = self.max_mana if player_data.mana is None else min(player_data.mana, self.max_mana)

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

        item_deltas = get_item_stats(equipped_name)
        if item_deltas:
            for stat, delta in item_deltas.items():
                effective_stats[stat] = effective_stats.get(stat, 0) + delta
        return effective_stats

    @staticmethod
    def calculate_hp(stats):
        # max(22, abs(Strength) * 0.95 + abs(Defense) * 2.3)
        return int(max(22, abs(int(stats['Strength'])) * 0.95 + abs(int(stats['Defense'])) * 2.3))


    @staticmethod
    def calculate_mana(stats):
        # max(20, abs(Intelligence) * 4.5)
        return int(max(20, abs(int(stats['Intelligence'])) * 4.5))



    @staticmethod
    def _resolve_current_hp(saved_hp, saved_max_hp, new_max_hp):
        """Preserve damage taken across max_hp changes (formula tweaks, stat changes) by
        healing the difference when max_hp increases, instead of leaving HP stranded below the new cap."""
        hp_gain = max(0, new_max_hp - (saved_max_hp if saved_max_hp is not None else new_max_hp))
        return min(new_max_hp, saved_hp + hp_gain)

    def player_data(self):
        carried = {f.name: getattr(self, f.name) for f in fields(PlayerData) if f.name not in self.DERIVED_FIELDS}
        return PlayerData(**carried, hp=self.current_hp, mana=self.current_mana, max_hp=self.max_hp,
                          stats=self.base_stats)

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

        offensive_stats = {k: v for k, v in stats.items() if k != 'Defense'}
        highest_stat_value = max(offensive_stats.values())

        strength_bonus = stats.get('Strength', 0) * str_percent

        luck_stat = stats.get('Luck', 0)
        luck_random_roll = random.randint(*luck_range)
        luck_bonus = luck_random_roll * (luck_stat / 10)

        total_damage = highest_stat_value + strength_bonus + luck_bonus
        return round(total_damage, 2)
