from enemies.enemies_data import (
    MIN_ENCOUNTER_WEIGHT,
    get_encounter_enemy,
    get_encounter_weight,
    get_encounter_weights,
    get_enemy_difficulty,
    get_enemy_stats,
)

LEVEL_1_POWER = 31  # roughly a fresh Warrior (sum of abs base stats)


def test_difficulty_is_sum_of_absolute_stats_without_name():
    # Skeleton: Corruption 0, HP 18, Attack 8, Defense 14, Speed 3, Luck 4 -> 47
    assert get_enemy_difficulty(get_enemy_stats("Skeleton")) == 47


def test_difficulty_counts_negative_stats_as_positive():
    stats = {"Name": "X", "HP": 10, "Attack": -5, "Speed": -3}
    assert get_enemy_difficulty(stats) == 18


def test_enemy_far_above_target_is_much_rarer_than_one_at_target():
    at_target = get_encounter_weight(LEVEL_1_POWER * 2.5, LEVEL_1_POWER)
    dragon = get_encounter_weight(get_enemy_difficulty(get_enemy_stats("Dragon")), LEVEL_1_POWER)
    assert at_target == 1
    assert dragon < at_target / 100


def test_weak_enemies_fade_but_never_vanish():
    trivial = get_encounter_weight(1, 200)
    assert 0 < trivial < 1
    assert trivial >= MIN_ENCOUNTER_WEIGHT


def test_same_enemy_becomes_more_likely_as_player_grows():
    dragon_difficulty = get_enemy_difficulty(get_enemy_stats("Dragon"))
    assert get_encounter_weight(dragon_difficulty, 226) > get_encounter_weight(dragon_difficulty, 31)


def test_weights_are_all_positive_even_for_a_zero_power_player():
    weights = get_encounter_weights(0)
    assert weights and all(weight > 0 for _, weight in weights)


def test_get_encounter_enemy_returns_a_real_enemy():
    known = {name for name, _ in get_encounter_weights(LEVEL_1_POWER)}
    for _ in range(50):
        assert get_encounter_enemy(LEVEL_1_POWER) in known
