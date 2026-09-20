from combat.combat_player import Player
from players.player_data import PlayerData


def test_calculate_hp_normal_stats():
    # 10 Strength, 10 Defence -> abs(10)*0.95 + abs(10)*2.3 = 9.5 + 23 = 32.5 -> int() truncates to 32
    stats = {'Strength': 10, 'Defence': 10}
    assert Player.calculate_hp(stats) == 32


def test_calculate_hp_floor_applies_at_zero():
    # 0 Strength, 0 Defence -> formula gives 0, but HP can never go below the 22 floor
    stats = {'Strength': 0, 'Defence': 0}
    assert Player.calculate_hp(stats) == 22


def test_calculate_hp_uses_absolute_value_for_negative_stats():
    # Negative stats should contribute the same HP as their positive counterparts
    stats = {'Strength': -10, 'Defence': -10}
    assert Player.calculate_hp(stats) == 32


def test_player_data_round_trip_preserves_exp():
    # _do_save() wraps PlayerData into a Player then calls .player_data() again before
    # writing to disk. Any field Player doesn't explicitly carry through both steps
    # silently resets to its dataclass default on every save — this caught exactly
    # that bug for `exp` when it was first added.
    original = PlayerData(
        name='RoundTrip', role='mage', level=3, hp=20, max_hp=25,
        stats={'Strength': 4, 'Agility': 4, 'Intelligence': 12, 'Defence': 4, 'Magic': 6, 'Luck': 3},
        gold=50, loot=['Iron Sword'], equipped=None, exp=42.5,
    )

    round_tripped = Player(original).player_data()

    assert round_tripped.exp == 42.5
    assert round_tripped.gold == 50
    assert round_tripped.loot == ['Iron Sword']
