"""v1.1 enemies with brains: phases, charges, defending, counters, group support and heals, fleeing"""
import pytest

from combat import enemy_brain
from combat.combat import Combat, Enemy, start_combat
from combat.damage_calculator import DamageCalculator as DC
from combat.enemy_brain import (BRAIN, CHARGE_BIDING, CHARGE_READY, CHARGING_ODDS, SOLO_ODDS, SUPPORT_ODDS,
                                decide, heal_target, leader, phase)
from players.player_data import PlayerData

STATS = {'Strength': 5, 'Agility': 5, 'Intelligence': 0, 'Charisma': 0, 'Defense': 5, 'Magic': 5, 'Luck': 5}


def player(**overrides):
    defaults = dict(name="T", role="warrior", level=1, hp=40, stats=dict(STATS), max_hp=40, in_town=False, distance=1)
    defaults.update(overrides)
    return PlayerData(**defaults)


def enemy(name="Bandit", hp_share=1.0):
    e = Enemy(name)
    e.hp = round(e.max_hp * hp_share)
    return e


@pytest.fixture
def table(monkeypatch):
    """pick() returns the odds table it was given, so tests can see which one a decision used"""
    monkeypatch.setattr(enemy_brain, "pick", lambda odds: odds)


@pytest.fixture
def rolls(monkeypatch):
    """Script BRAIN.uniform: rolls.set(5, 99, ...) — after they run out, 99 (nothing procs)"""
    class Rolls:
        def set(self, *values):
            it = iter(values)
            monkeypatch.setattr(BRAIN, "uniform", lambda a, b: next(it, 99))
    r = Rolls()
    r.set()
    return r


# --- formulas -------------------------------------------------------------------------------------

def test_formulas():
    assert [DC.enemy_defend_block(d) for d in (0, 13, 15, 35, 100, 150)] == [1, 1, 2, 3, 8, 11]
    assert DC.enemy_defend_block(-10) == 0                      # too reckless to guard
    assert DC.enemy_counter_bonus(13) == 5 and DC.enemy_counter_bonus(100) == 12 and DC.enemy_counter_bonus(-5) == 0
    assert DC.enemy_flee_chance(20, 17) == 15 and DC.enemy_flee_chance(15, 0) == 6 and DC.enemy_flee_chance(-5, 0) == 0
    assert DC.enemy_heal_chance(-5, 0) == 35 and DC.enemy_heal_chance(17, 20) == 53.5 and DC.enemy_heal_chance(50, 60) == 75


def test_phases():
    assert phase(enemy(hp_share=1)) == 1 and phase(enemy(hp_share=0.8)) == 1
    assert phase(enemy(hp_share=0.75)) == 2 and phase(enemy(hp_share=0.5)) == 2
    assert phase(enemy(hp_share=0.45)) == 3


# --- solo decisions --------------------------------------------------------------------------------

def test_solo_odds_follow_its_hp(table, rolls):
    for share, p in ((1, 1), (0.6, 2), (0.3, 3)):
        e = enemy(hp_share=share)
        assert decide(e, [e]) is SOLO_ODDS[p]


def test_phase_3_tries_to_flee_first(rolls):
    e = enemy("Wolf", 0.3)                    # Speed 20 + Luck 17: 15%
    rolls.set(14.9)
    assert decide(e, [e]) == "flee"
    rolls.set(15)
    assert decide(e, [e]) != "flee"
    healthy = enemy("Wolf", 0.6)
    rolls.set(0)
    assert decide(healthy, [healthy]) != "flee"


def test_special_fights_never_flee(rolls):
    e = enemy("Wolf", 0.1)
    rolls.set(0)
    assert decide(e, [e], can_flee=False) != "flee"
    assert not Combat(player(), "Wolf", special=True).enemies_can_flee
    assert not Combat(player(), "Mimic").enemies_can_flee      # never-random enemies, special or not
    assert Combat(player(), "Wolf").enemies_can_flee


def test_a_charge_bides_then_moves_then_lands(table, rolls):
    e = enemy("Wolf", 0.1)
    e.charge = CHARGE_BIDING
    rolls.set(0)
    assert decide(e, [e]) is CHARGING_ODDS[3]                   # charging: no fleeing, just attack/defend
    e.charge = CHARGE_READY
    assert decide(e, [e]) == "release"


# --- groups -----------------------------------------------------------------------------------------

def test_healthy_group_leader_and_support(table, rolls):
    a, b = enemy(hp_share=1), enemy(hp_share=0.9)
    assert leader([a, b]) is a
    assert decide(a, [a, b]) is SOLO_ODDS[1]
    assert decide(b, [a, b]) is SUPPORT_ODDS[1]


def test_hurt_group(table, rolls):
    healthy, hurt = enemy(hp_share=0.9), enemy(hp_share=0.6)
    assert decide(hurt, [healthy, hurt]) is SOLO_ODDS[2]       # the hurt one acts on its own phase
    assert decide(healthy, [healthy, hurt]) is SUPPORT_ODDS[2]


def test_heal_without_anyone_to_heal_attacks_instead(monkeypatch, rolls):
    monkeypatch.setattr(enemy_brain, "pick", lambda odds: "heal")
    healer, hurt = enemy("Bat", 0.9), enemy("Bat", 0.6)        # Bats are -Attack: can't be healed
    assert decide(healer, [healer, hurt]) == "attack"


def test_heal_targets(rolls):
    healer, weakest, boss = enemy(hp_share=0.85), enemy(hp_share=0.3), enemy(hp_share=0.9)
    alive = [healer, weakest, boss]
    rolls.set(10)                     # under 65: the most hurt member
    assert heal_target(healer, alive) is weakest
    rolls.set(80)                     # otherwise the leader
    assert heal_target(healer, alive) is boss
    assert heal_target(healer, [healer]) is None               # never itself


# --- actions in combat ---------------------------------------------------------------------------------

def fight_with(monkeypatch, actions, name="Bandit", size=1, **kw):
    combat = Combat(player(**kw), name, size)
    it = iter(actions)
    monkeypatch.setattr(enemy_brain, "decide", lambda e, enemies, can_flee=True: next(it))
    combat.current_turn, combat.current_enemy_index = "enemy", 0
    return combat


def test_charge_flow_in_combat(monkeypatch):
    combat = fight_with(monkeypatch, ["charge", "defend", "release"])
    hits = []
    monkeypatch.setattr(Combat, "enemy_attack", lambda self, e, scale=1.0, bonus=0: hits.append((scale, bonus)))
    e = combat.enemies[0]
    combat.enemy_turn()
    assert e.charge == CHARGE_BIDING
    combat.current_turn, combat.current_enemy_index = "enemy", 0
    combat.enemy_turn()
    assert e.defending and e.charge == CHARGE_READY
    combat.current_turn, combat.current_enemy_index = "enemy", 0
    combat.enemy_turn()
    assert e.charge == 0 and not e.defending and hits == [(1.5, 0)]


def test_a_minus_attack_charge_sears(monkeypatch):
    combat = fight_with(monkeypatch, ["release"], name="Vampire")
    monkeypatch.setattr(Combat, "enemy_attack", lambda self, e, scale=1.0, bonus=0: None)
    combat.enemies[0].charge = CHARGE_READY
    hp = combat.player.current_hp
    combat.enemy_turn()
    assert hp - combat.player.current_hp == round(DC.siphon_amount(-15) * 1.3)     # 9


def test_defending_blocks_physical_only():
    combat = Combat(player(), "Bandit")                          # Defense 13: blocks 1
    e = combat.enemies[0]
    e.defending = True
    normal, _ = DC.enemy_defence_adjustment(20, 13, "physical")
    assert combat._hit_enemy(e, 20, "physical") == pytest.approx(normal - 1)
    spell, _ = DC.enemy_defence_adjustment(20, 13, "spell")
    assert combat._hit_enemy(e, 20, "spell") == pytest.approx(spell)


def test_reckless_minus_defense_enemies_dont_block():
    combat = Combat(player(), "Rustbound Automaton")             # Defense -10
    e = combat.enemies[0]
    e.defending = True
    expected, _ = DC.enemy_defence_adjustment(10, -10, "physical")
    assert combat._hit_enemy(e, 10, "physical") == pytest.approx(expected)


def test_a_defending_enemy_counters(monkeypatch, rolls):
    combat = Combat(player(), "Bandit")
    e = combat.enemies[0]
    e.defending = True
    hits = []
    monkeypatch.setattr(Combat, "enemy_attack", lambda self, en, scale=1.0, bonus=0: hits.append(bonus))
    rolls.set(14.9)
    combat._hit_enemy(e, 5, "physical")
    rolls.set(15)
    combat._hit_enemy(e, 5, "physical")
    combat._hit_enemy(e, 5, "spell")
    assert hits == [5]                                           # once, with the Defense bonus


def test_a_minus_attack_counter_lands_with_its_siphon(monkeypatch):
    combat = Combat(player(stats=dict(STATS, Agility=0, Defense=0)), "Leech")   # Attack -22, Defense 13
    monkeypatch.setattr("combat.combat.DamageCalculator.calculate_enemy_damage",
                        lambda stats, name: (0, [("leech_on_hit", 10.1)]))
    monkeypatch.setattr("combat.combat.DamageCalculator.calculate_damage_taken",
                        lambda damage, *a, **k: (damage, []))
    hp = combat.player.current_hp
    combat.enemy_attack(combat.enemies[0], bonus=5)
    assert hp - combat.player.current_hp == pytest.approx(15, abs=0.5)   # 5 bonus + its ~10 siphon


def test_heals(monkeypatch, rolls):
    combat = fight_with(monkeypatch, ["heal", "heal"], size=2)
    healer, hurt = combat.enemies
    hurt.hp = 5
    rolls.set(10, 0)                                             # target: the most hurt; heal lands
    combat.enemy_turn()
    assert hurt.hp == 5 + round(hurt.max_hp * 0.12)
    combat.current_turn, combat.current_enemy_index = "enemy", 0
    before = hurt.hp
    rolls.set(10, 99)                                            # fumbles
    combat.enemy_turn()
    assert hurt.hp == before


# --- fleeing ---------------------------------------------------------------------------------------------

def test_a_solo_enemy_running_off_ends_the_fight(monkeypatch, rolls):
    pd = player(gold=0)
    monkeypatch.setattr(enemy_brain, "decide", lambda e, enemies, can_flee=True: "flee")
    monkeypatch.setattr("builtins.input", lambda *_: "3")       # you defend, it runs
    rolls.set(0)                                                 # it drops something...
    monkeypatch.setattr(BRAIN, "random", lambda: 0.1)            # ...gold
    monkeypatch.setattr(BRAIN, "randint", lambda a, b: 6)
    outcome = start_combat(pd, "Bandit")
    assert outcome[0] == "enemy_fled" and outcome.fled == 1 and pd.gold == 6


def test_fleeing_gives_no_rewards_and_ticks_nothing(monkeypatch):
    from combat.combat import FightResult
    from game.pyrpg import PYRPG
    game = PYRPG.__new__(PYRPG)
    game.player_data = player(gold=0, exp=0)
    game.saving_enabled = False
    monkeypatch.setattr("game.pyrpg.start_combat", lambda *a, **k: FightResult("enemy_fled", 30, None, fled=1))
    monkeypatch.setattr("builtins.input", lambda *_: "")
    seen = []
    game.events.on("victory", lambda **kw: seen.append(kw))
    game.fight("Wolf", special=False)
    assert game.player_data.gold == 0 and game.player_data.exp == 0 and seen == []


def test_part_of_a_group_fleeing_pays_only_for_the_ones_you_beat(monkeypatch):
    from combat.combat import FightResult
    from game.pyrpg import PYRPG
    game = PYRPG.__new__(PYRPG)
    game.player_data = player()
    game.saving_enabled = False
    monkeypatch.setattr("game.pyrpg.start_combat", lambda *a, **k: FightResult("victory", 30, None, fled=1))
    monkeypatch.setattr("builtins.input", lambda *_: "")
    monkeypatch.setattr(PYRPG, "calculate_gold_reward", lambda self: 10)
    seen = []
    game.events.on("victory", lambda enemy, size: seen.append(size))
    game.fight("Wolf", 3, special=False)
    assert game.player_data.gold == 20 and seen == [2]


def test_fled_enemies_drop_out_of_the_fight(monkeypatch):
    combat = Combat(player(), "Wolf", 2)
    combat.enemies[0].fled = True
    assert not combat.enemies[0].is_alive()
    combat.enemies[1].hp = 0
    combat._check_victory()
    assert combat.run_combat()[0] == "victory"


def test_fled_lines_by_looks(monkeypatch):
    from util import flavor
    monkeypatch.setattr(flavor._rng, "uniform", lambda a, b: 0)
    monkeypatch.setattr(flavor._rng, "choice", lambda seq: seq[0])
    assert "ugly" in flavor.fled_line("Wolf", None, -3)
    assert "handsome" not in flavor.fled_line("Wolf", None, 3) and "afraid" in flavor.fled_line("Wolf", None, 3)
    assert "shiny 5 gold" in flavor.fled_line("Wolf", "5 gold", 9)
