from game.pyrpg import PYRPG
from players.player_data import PlayerData

BASE_STATS = {'Strength': 5, 'Agility': 5, 'Intelligence': 0, 'Defence': 5, 'Magic': 5, 'Luck': 5}


def make_game(**stat_overrides):
    """A PYRPG without running its interactive __init__."""
    game = PYRPG.__new__(PYRPG)
    game.player_data = PlayerData(name="T", role="warrior", level=1, hp=30, stats={**BASE_STATS, **stat_overrides})
    return game


def test_rest_chance_has_a_20_percent_floor():
    for luck in (0, 5, 20):
        assert make_game(Luck=luck).calculate_rest_chance() == 20


def test_rest_chance_scales_with_luck_between_floor_and_cap():
    assert make_game(Luck=40).calculate_rest_chance() == 40


def test_rest_chance_is_capped_at_60():
    assert make_game(Luck=100).calculate_rest_chance() == 60


def test_rest_chance_is_flat_20_for_negative_luck():
    assert make_game(Luck=-1).calculate_rest_chance() == 20
    assert make_game(Luck=-40).calculate_rest_chance() == 20


def test_negative_magic_earns_15_percent_less_exp():
    normal = make_game(Magic=5).calculate_exp_reward("Bandit")
    cursed = make_game(Magic=-5).calculate_exp_reward("Bandit")
    assert cursed == normal * 0.85


def test_zero_magic_is_not_penalised():
    assert make_game(Magic=0).calculate_exp_reward("Bandit") == make_game(Magic=5).calculate_exp_reward("Bandit")


def test_player_power_is_sum_of_absolute_effective_stats():
    game = make_game(Strength=-3)  # -3 + 5 + 0 + 5 + 5 + 5 -> 3 + 5 + 0 + 5 + 5 + 5
    game.player_data.equipped = None
    assert game._player_power() == 23
