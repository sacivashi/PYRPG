from enemies.enemies_data import (
    MIN_ENCOUNTER_WEIGHT,
    THREAT_WEIGHTS,
    get_encounter_enemy,
    get_encounter_weight,
    get_encounter_weights,
    get_enemy_difficulty,
    get_enemy_stats,
    get_enemy_threat,
)

LEVEL_1_POWER = 31  # roughly a fresh Warrior (sum of abs base stats)


# --- get_enemy_difficulty: drives EXP, every stat counts equally, unaffected by threat weighting ---

def test_difficulty_is_sum_of_absolute_stats_without_name():
    # Skeleton: Corruption 0, HP 18, Attack 8, Defense 14, Speed 3, Luck 4 -> 47
    assert get_enemy_difficulty(get_enemy_stats("Skeleton")) == 47


def test_difficulty_counts_negative_stats_as_positive():
    stats = {"Name": "X", "HP": 10, "Attack": -5, "Speed": -3}
    assert get_enemy_difficulty(stats) == 18


# --- get_enemy_threat: drives encounter matching, HP/Attack weighted higher than Speed/Luck ---

def test_threat_applies_the_documented_weights():
    stats = {"Name": "X", "HP": 10, "Attack": 10, "Defense": 10, "Speed": 10, "Luck": 10, "Corruption": 10}
    expected = sum(10 * w for w in THREAT_WEIGHTS.values())
    assert get_enemy_threat(stats) == expected


def test_fast_lucky_but_fragile_enemy_reads_as_low_threat():
    # Goblin: 10 HP, 3 Attack, but 60 Speed and 50 Luck — difficulty treats it as mid-tier,
    # threat should not, since HP/Attack are what actually make a fight dangerous.
    goblin = get_enemy_stats("Goblin")
    assert get_enemy_difficulty(goblin) > 100
    assert get_enemy_threat(goblin) < get_enemy_difficulty(goblin) / 2


def test_high_hp_attack_enemy_stays_high_threat_relative_to_difficulty():
    # Dragon barely loses any weight, since HP/Attack dominate its stat line already
    dragon = get_enemy_stats("Dragon")
    assert get_enemy_threat(dragon) > get_enemy_difficulty(dragon) * 0.7


# --- get_encounter_weight / get_encounter_weights / get_encounter_enemy: use threat, not difficulty ---

def test_enemy_far_above_target_is_much_rarer_than_one_at_target():
    at_target = get_encounter_weight(LEVEL_1_POWER * 2.5, LEVEL_1_POWER)
    dragon = get_encounter_weight(get_enemy_threat(get_enemy_stats("Dragon")), LEVEL_1_POWER)
    assert at_target == 1
    assert dragon < at_target / 100


def test_weak_enemies_fade_but_never_vanish():
    trivial = get_encounter_weight(1, 200)
    assert 0 < trivial < 1
    assert trivial >= MIN_ENCOUNTER_WEIGHT


def test_same_enemy_becomes_more_likely_as_player_grows():
    dragon_threat = get_enemy_threat(get_enemy_stats("Dragon"))
    assert get_encounter_weight(dragon_threat, 226) > get_encounter_weight(dragon_threat, 31)


def test_weights_are_all_positive_even_for_a_zero_power_player():
    weights = get_encounter_weights(0)
    assert weights and all(weight > 0 for _, weight in weights)


def test_get_encounter_enemy_returns_a_real_enemy():
    known = {name for name, _ in get_encounter_weights(LEVEL_1_POWER)}
    for _ in range(50):
        assert get_encounter_enemy(LEVEL_1_POWER) in known


def test_goblin_is_now_a_more_common_encounter_than_the_old_difficulty_score_gave_it():
    # Goblin's difficulty (124, from its 60 Speed/50 Luck) sat above a level-1 target of 77.5,
    # which used to make it fade out like a genuinely tougher-than-you enemy. Its threat (46.5)
    # sits below target instead, correctly reading as the easy, common enemy its 10 HP suggests.
    goblin = get_enemy_stats("Goblin")
    old_weight = get_encounter_weight(get_enemy_difficulty(goblin), LEVEL_1_POWER)
    new_weight = get_encounter_weight(get_enemy_threat(goblin), LEVEL_1_POWER)
    assert new_weight > old_weight
