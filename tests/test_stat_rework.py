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
    assert DamageCalculator.player_damage_reduction(8) == (2 + 8 * 0.7) / 100   # was 80% before v1.0
    assert DamageCalculator.player_damage_reduction(12) == (2 + 12 * 0.7) / 100
    assert DamageCalculator.player_damage_reduction(33) == 0.25
    assert DamageCalculator.player_damage_reduction(0) == 0
    assert DamageCalculator.player_damage_reduction(-5) == 0


def test_enemy_defense_reduces_physical_more_than_spells():
    physical, _ = DamageCalculator.enemy_defence_adjustment(100, 13, "physical")   # min(20, 13.7)%
    spell, _ = DamageCalculator.enemy_defence_adjustment(100, 13, "spell")         # min(15, 3.6)%
    assert round(physical, 2) == 86.3
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


# --- Arrowshot (Ranger's basic attack) -----------------------------------------------------------

RANGER = {'Strength': 3, 'Agility': 11, 'Intelligence': 6, 'Defence': 2, 'Magic': 2, 'Luck': 9}


def test_arrowshot_formula():
    assert DamageCalculator.ability_damage("Arrowshot", RANGER) == int(11 * 0.7 + 2 * 0.3) == 8
    assert DamageCalculator.ability_damage("Arrowshot", {**RANGER, 'Agility': 30, 'Magic': -6}) == int(21 + 1.8) == 22


def test_arrowshot_is_a_5_mana_ability_dealt_as_magic_damage(monkeypatch):
    monkeypatch.setattr("combat.combat.random.randint", lambda a, b: b)   # no mana waste
    combat = make_combat(RANGER, enemy="Skeleton", role="ranger", known_spells=["Arrowshot"])   # Defense 14
    hp_before, mana_before = combat.enemies[0].hp, combat.player.current_mana
    combat.cast("Arrowshot")
    spell_hit = DamageCalculator.enemy_defence_adjustment(8, 14, "spell")[0]
    assert combat.enemies[0].hp == max(0, round(hp_before - spell_hit))
    assert combat.player.current_mana == mana_before - 5


def test_rangers_start_knowing_arrowshot():
    from game.pyrpg import PYRPG
    game = PYRPG.__new__(PYRPG)
    game.player_data = PlayerData(name="T", role="ranger", level=1, hp=22, stats=dict(RANGER), max_hp=22)
    game._learn_level_up_spells()
    assert game.player_data.known_spells == ["Arrowshot"]



# --- v1.0 abilities ------------------------------------------------------------------------------

def test_ability_formulas():
    stats = {'Strength': 6, 'Agility': 9, 'Intelligence': 4, 'Defence': 12, 'Magic': 3, 'Luck': 1}
    assert DamageCalculator.ability_damage("Backstab", stats) == int(15 + 9 * 0.8) == 22
    assert DamageCalculator.ability_damage("Blade bonk", stats) == int(5 + 6 * 0.55) == 8
    assert DamageCalculator.ability_damage("Shield bash", stats) == int(12 * 1.5) == 18
    assert DamageCalculator.ability_damage("Shield bash", {**stats, 'Defence': -9}) == 0   # no negative hits


def test_backstab_searing_ignores_defense_and_corruption(monkeypatch):
    monkeypatch.setattr("combat.combat.random.randint", lambda a, b: b)
    rogue = {'Strength': 5, 'Agility': 9, 'Intelligence': 5, 'Defence': 4, 'Magic': 2, 'Luck': 9}
    combat = make_combat(rogue, enemy="Dragon", role="rogue", known_spells=["Backstab"])
    dragon = combat.enemies[0]
    dragon.corruption = 50                                   # would swallow any normal hit
    before = dragon.hp
    combat.cast("Backstab")
    assert dragon.hp == before - 22


def test_shield_bash_is_physical(monkeypatch):
    monkeypatch.setattr("combat.combat.random.randint", lambda a, b: b)
    tank = {'Strength': 0, 'Agility': -5, 'Intelligence': 2, 'Defence': 12, 'Magic': 1, 'Luck': 5}
    combat = make_combat(tank, enemy="Skeleton", role="tank", known_spells=["Shield bash"])   # Defense 14
    before = combat.enemies[0].hp
    combat.cast("Shield bash")
    expected = DamageCalculator.enemy_defence_adjustment(18, 14, "physical")[0]
    assert combat.enemies[0].hp == max(0, round(before - expected))


def test_berserk_scream_boosts_physical_hits_and_drains_intelligence(monkeypatch):
    monkeypatch.setattr("combat.combat.random.randint", lambda a, b: b)
    dwarf = {'Strength': 7, 'Agility': 3, 'Intelligence': 5, 'Defence': 7, 'Magic': 3, 'Luck': 0}
    combat = make_combat(dwarf, enemy="Dragon", role="dwarf", known_spells=["Berserk scream"])
    combat.cast("Berserk scream")
    assert combat.berserk_bonus == int(max(1, 7 * 0.45)) == 3
    assert combat.player.stats['Intelligence'] == 5 - int(combat.player.max_hp * 0.80)
    assert combat.cast("Berserk scream") is None                  # once per combat
    monkeypatch.setattr(DamageCalculator, "calculate_player_damage", staticmethod(lambda stats: (12, True)))
    before = combat.enemies[0].hp
    combat.player_attack()
    expected = DamageCalculator.enemy_defence_adjustment(12 + 3, combat.enemies[0].stats['Defense'], "physical")[0]
    assert combat.enemies[0].hp == round(before - expected)


def test_berserk_bonus_has_a_floor_of_1():
    assert DamageCalculator.berserk_bonus(-10) == 1
    assert DamageCalculator.berserk_bonus(22) == 9


# --- Defend --------------------------------------------------------------------------------------

def test_defend_block_formula():
    assert DamageCalculator.defend_block(12) == 9
    assert DamageCalculator.defend_block(20) == 10          # capped
    assert DamageCalculator.defend_block(-9) == 0           # -Defence blocks nothing


def test_defending_blocks_every_hit_until_your_next_turn(monkeypatch):
    tank = {'Strength': 0, 'Agility': 5, 'Intelligence': 2, 'Defence': 12, 'Magic': 1, 'Luck': 5}
    combat = make_combat(tank, enemy="Bear")
    monkeypatch.setattr(DamageCalculator, "calculate_enemy_damage", staticmethod(lambda stats, name: (20, [])))
    monkeypatch.setattr(DamageCalculator, "roll_dodge", staticmethod(lambda bonus, agility=0: (False, False)))
    combat.player_defend()
    hp = combat.player.current_hp
    combat.enemy_attack(combat.enemies[0])
    combat.enemy_attack(combat.enemies[0])                 # a second hit is still blocked
    one_hit = round(20 * (1 - DamageCalculator.player_damage_reduction(12)) - 9, 2)   # % first, then the 9 block
    assert combat.player.current_hp == round(round(hp - one_hit) - one_hit)


def test_defend_ends_when_your_turn_comes_back(monkeypatch):
    combat = make_combat()
    combat.player_defend()
    monkeypatch.setattr("builtins.input", lambda *_: "4")   # skip
    combat.current_turn = "player"
    combat.player_turn()
    assert combat.defending is False
