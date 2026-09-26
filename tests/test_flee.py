from combat.combat import Combat
from combat.damage_calculator import DamageCalculator
from players.player_data import PlayerData
from roles.roles_data import RolesExtract


def flee(agility, enemy_speed=0):
    return DamageCalculator.calculate_flee_chance(agility, enemy_speed)


def test_continuous_through_25_percent_at_agility_zero():
    assert flee(0) == 25


def test_positive_agility_scales_up_to_a_60_percent_cap():
    assert flee(1) == 27
    assert flee(11) == 47
    assert flee(17) == 59
    assert flee(18) == 60
    assert flee(100) == 60


def test_negative_agility_scales_down_to_a_20_percent_floor():
    assert flee(-1) == 24.8
    assert flee(-20) == 20
    assert flee(-100) == 20


def test_no_cliff_at_the_agility_zero_boundary():
    # The old formula jumped from 25% at 0 to 59% at -1; this one should step smoothly instead
    assert abs(flee(0) - flee(-1)) < 1
    assert abs(flee(0) - flee(1)) < 3


def test_negative_speed_enemy_adds_a_bonus_on_top_of_the_base_chance():
    assert flee(0, enemy_speed=-10) == 25 + 3      # min(15, 10*0.3) = 3
    assert flee(0, enemy_speed=-60) == 25 + 15      # capped at +15
    assert flee(0, enemy_speed=5) == 25             # positive Speed gives no bonus


def test_flee_chance_never_exceeds_100():
    # 60 (Agility cap) + 15 (Speed bonus cap) = 75 is the actual achievable maximum
    assert DamageCalculator.calculate_flee_chance(100, -1000) == 75


def test_stock_roles_land_between_the_floor_and_cap():
    for role, stats in RolesExtract.get_role_stats_by_name().items():
        chance = flee(stats['Agility'])
        assert 20 <= chance <= 60, f"{role}: {chance}%"


STATS = {'Strength': 2, 'Agility': 0, 'Intelligence': 2, 'Defence': 2, 'Magic': 2, 'Luck': 2}
NATURAL_MAX_HP = 22  # what calculate_hp gives for STATS regardless of Agility


def make_combat(agility, enemy_speed=0, hp=NATURAL_MAX_HP):
    # max_hp must match what calculate_hp actually produces for these stats, or
    # _resolve_current_hp reads the mismatch as "max HP grew" and heals the difference
    stats = {**STATS, 'Agility': agility}
    pd = PlayerData(name="T", role="warrior", level=1, hp=hp, stats=stats, max_hp=NATURAL_MAX_HP)
    combat = Combat(pd, "Bandit")
    combat.enemies[0].stats['Speed'] = enemy_speed
    return combat


def test_successful_flee_ends_combat_with_fled_result(monkeypatch):
    combat = make_combat(agility=100)  # 60% capped chance, but we force the roll anyway
    monkeypatch.setattr("random.randint", lambda a, b: 1)  # guarantees success (roll <= chance)
    fled = combat.attempt_flee()
    assert fled is True
    assert combat.player_fled is True
    assert combat.combat_ongoing is False


def test_failed_flee_does_not_end_combat(monkeypatch):
    combat = make_combat(agility=-100)  # 20% floor chance
    monkeypatch.setattr("random.randint", lambda a, b: 100)  # guarantees failure
    fled = combat.attempt_flee()
    assert fled is False
    assert combat.player_fled is False
    assert combat.combat_ongoing is True


def test_run_combat_reports_fled_with_no_hp_change():
    # hp starts below the natural max (22) so a "no change" bug (topped up, or clamped down)
    # would actually show up instead of coincidentally matching
    combat = make_combat(agility=0, hp=15)
    combat.player_fled = True
    combat.combat_ongoing = False  # loop body never runs; goes straight to the end-of-combat result
    result, hp = combat.run_combat()
    assert result == "fled"
    assert hp == 15


def test_fled_grants_no_gold_exp_or_loot(monkeypatch):
    from game.pyrpg import PYRPG
    game = PYRPG.__new__(PYRPG)
    game.player_data = PlayerData(name="T", role="warrior", level=1, hp=30,
                                   stats={'Strength': 5, 'Agility': 5, 'Intelligence': 0,
                                          'Defence': 5, 'Magic': 5, 'Luck': 5}, max_hp=30)
    monkeypatch.setattr("game.pyrpg.start_combat", lambda player_data, enemy_name, group_size: ("fled", 30))
    monkeypatch.setattr("game.pyrpg.get_encounter_enemy", lambda power: "Bandit")
    monkeypatch.setattr(game, "auto_save_player_state", lambda: None)
    monkeypatch.setattr("builtins.input", lambda *_: "")

    game.enter_combat()

    assert game.player_data.gold == 0
    assert game.player_data.exp == 0
    assert game.player_data.loot == []
