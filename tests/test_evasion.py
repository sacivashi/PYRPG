import random

from combat.damage_calculator import DamageCalculator


def test_evasion_scales_4_percent_per_agility_point():
    assert DamageCalculator.calculate_evasion_chance(5) == 5 * 0.04


def test_evasion_is_capped_at_35_percent():
    assert DamageCalculator.EVASION_CAP == 0.35
    for agility in (9, 11, 50, 1000):
        assert DamageCalculator.calculate_evasion_chance(agility) == 0.35


def test_no_evasion_from_zero_or_negative_agility():
    assert DamageCalculator.calculate_evasion_chance(0) == 0
    assert DamageCalculator.calculate_evasion_chance(-10) == 0


def test_high_agility_defender_dodges_about_35_percent_of_hits():
    random.seed(1234)
    stats = {'Agility': 20, 'Defence': 0}
    hits = 20000
    dodges = sum(
        1 for _ in range(hits)
        if DamageCalculator.calculate_damage_taken(10, stats)[1] == [("dodged", True)]
    )
    assert 0.33 < dodges / hits < 0.37
