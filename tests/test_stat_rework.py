from combat.combat import Combat
from combat.damage_calculator import DamageCalculator
from players.player_data import PlayerData

STATS = {'Strength': 5, 'Agility': 0, 'Intelligence': 0, 'Defence': 5, 'Magic': 0, 'Luck': 0}


def make_combat(stats=STATS, enemy="Bandit", **overrides):
    defaults = dict(name="T", role="warrior", level=1, hp=40, stats=dict(stats), max_hp=40)
    defaults.update(overrides)
    return Combat(PlayerData(**defaults), enemy)


# --- defence -----------------------------------------------------------------------------------

def test_player_defence_reduction_is_capped_at_25_percent():
    assert DamageCalculator.player_damage_reduction(8) == (1 + 8 * 0.9) / 100   # was 80% before v1.0
    assert DamageCalculator.player_damage_reduction(30) == 0.25
    assert DamageCalculator.player_damage_reduction(0) == 0
    assert DamageCalculator.player_damage_reduction(-5) == 0


def test_enemy_defense_reduces_physical_more_than_spells():
    physical, _ = DamageCalculator.enemy_defence_adjustment(100, 13, "physical")   # min(20, 9.8)%
    spell, _ = DamageCalculator.enemy_defence_adjustment(100, 13, "spell")         # min(15, 3.6)%
    assert round(physical, 2) == 90.2
    assert round(spell, 2) == 96.4
    assert DamageCalculator.enemy_defence_adjustment(100, 200, "physical")[0] == 80  # capped
    assert DamageCalculator.enemy_defence_adjustment(100, 200, "spell")[0] == 85
    assert DamageCalculator.enemy_defence_adjustment(100, 13, "item") == (100, 0)
    assert DamageCalculator.enemy_defence_adjustment(100, 0, "physical") == (100, 0)


def test_enemy_negative_defense_bonus_and_reflect():
    damage, reflected = DamageCalculator.enemy_defence_adjustment(20, -10, "physical")
    assert damage == 20 + 7.5                 # +max(3, 10 * 0.75)
    assert reflected == 20 * 4 / 100          # min(11, 10 * 0.4)% of the flat damage
    damage, reflected = DamageCalculator.enemy_defence_adjustment(20, -10, "spell")
    assert damage == 20 + 8.2 and reflected == 0


# --- corruption --------------------------------------------------------------------------------

def test_corruption_reduces_hits_and_weak_hits_heal():
    assert DamageCalculator.corruption_hit(20, 8) == (12, 0)
    assert DamageCalculator.corruption_hit(5, 8) == (0, 3)        # min(8 * 0.75, abs(5 - 8))
    assert DamageCalculator.corruption_hit(0, 50) == (0, 37.5)    # min(50 * 0.75, 50)


def test_corruption_tick_damage():
    assert DamageCalculator.corruption_tick_damage(200, 5) == 8
    assert DamageCalculator.corruption_tick_damage(20, 8) == 8
    assert DamageCalculator.corruption_tick_damage(10, 1) == 3


def test_corrupted_enemies_ignore_their_defense():
    combat = make_combat()
    target = combat.enemies[0]
    target.corruption = 5
    target.stats['Defense'] = 500
    dealt = combat._hit_enemy(target, 20, "physical")
    assert dealt == 15
    assert target.hp == target.max_hp - 15


# --- -Strength ---------------------------------------------------------------------------------

def test_strength_curse_formulas():
    assert DamageCalculator.strength_self_damage(-10, 40) == 11   # int(10 + int(min(3.2, 10) * 0.5))
    assert DamageCalculator.strength_self_damage(5, 40) == 0
    assert DamageCalculator.strength_heal(-10, 25, 10) == 13       # int(min(28, 13))


def test_strength_curse_sears_you_even_on_a_miss(monkeypatch):
    combat = make_combat({**STATS, 'Strength': -10})
    monkeypatch.setattr(DamageCalculator, "calculate_player_damage", staticmethod(lambda stats: (0, False)))
    start = combat.player.current_hp
    combat.player_attack()
    self_damage = DamageCalculator.strength_self_damage(-10, combat.player.max_hp)
    assert combat.player.current_hp == start - self_damage   # self-damage, no heal


def test_strength_curse_heals_after_a_landed_hit(monkeypatch):
    combat = make_combat({**STATS, 'Strength': -10}, enemy="Dragon")
    monkeypatch.setattr(DamageCalculator, "calculate_player_damage", staticmethod(lambda stats: (30, True)))
    combat.player.current_hp = 15
    combat.player_attack()
    self_damage = DamageCalculator.strength_self_damage(-10, combat.player.max_hp)
    assert combat.player.current_hp > 15 - self_damage


# --- physical damage (v1.0) ----------------------------------------------------------------------

def test_physical_damage_formula():
    # int(sqrt(abs(Str) + abs(Agi) + abs(Lck) + abs(Def) + 15) * 2.2)
    stats = {'Strength': 6, 'Agility': 4, 'Intelligence': 4, 'Defence': 6, 'Magic': 3, 'Luck': 1}
    assert DamageCalculator.calculate_base_damage(stats) == int((17 + 15) ** 0.5 * 2.2) == 12


def test_negative_physical_stats_count_by_their_size():
    monk = {'Strength': 5, 'Agility': 5, 'Defence': -9, 'Luck': 1}
    mirrored = {'Strength': 5, 'Agility': 5, 'Defence': 9, 'Luck': 1}
    assert DamageCalculator.calculate_base_damage(monk) == DamageCalculator.calculate_base_damage(mirrored) == 13


def test_intelligence_and_magic_dont_add_physical_damage():
    plain = {'Strength': 5, 'Agility': 5, 'Defence': 5, 'Luck': 5, 'Intelligence': 0, 'Magic': 0}
    caster = {**plain, 'Intelligence': 50, 'Magic': 50}
    assert DamageCalculator.calculate_base_damage(plain) == DamageCalculator.calculate_base_damage(caster)


def test_zero_stats_still_hit_for_8():
    assert DamageCalculator.calculate_base_damage({}) == 8


def test_positive_luck_adds_no_random_bonus_anymore():
    stats = {'Strength': 5, 'Agility': 5, 'Defence': 5, 'Luck': 9}
    assert {DamageCalculator.calculate_player_damage(stats)[0] for _ in range(50)} == {DamageCalculator.calculate_base_damage(stats)}
