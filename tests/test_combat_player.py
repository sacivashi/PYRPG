from combat.combat_player import Player


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
