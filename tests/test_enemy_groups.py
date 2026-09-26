import random

from combat.combat import Combat, Enemy, GROUP_CHANCE, GROUP_SIZES, roll_group_size
from players.player_data import PlayerData

STATS = {'Strength': 5, 'Agility': 5, 'Intelligence': 0, 'Defence': 5, 'Magic': 5, 'Luck': 5}


def make_group_combat(size=3, enemy="Bandit", hp=999):
    pd = PlayerData(name="T", role="warrior", level=1, hp=hp, stats=dict(STATS), max_hp=hp)
    return Combat(pd, enemy, group_size=size)


# --- roll_group_size / Enemy basics -------------------------------------------------------

def test_roll_group_size_returns_1_or_a_group_size():
    for _ in range(200):
        size = roll_group_size()
        assert size == 1 or size in GROUP_SIZES


def test_roll_group_size_respects_the_flat_chance(monkeypatch):
    monkeypatch.setattr(random, "randint", lambda a, b: GROUP_CHANCE)  # right at the boundary -> triggers (<=)
    monkeypatch.setattr(random, "choice", lambda seq: seq[0])
    assert roll_group_size() == GROUP_SIZES[0]

    monkeypatch.setattr(random, "randint", lambda a, b: GROUP_CHANCE + 1)  # just past it -> solo
    assert roll_group_size() == 1


def test_enemy_instances_have_independent_stats():
    a = Enemy("Bandit")
    b = Enemy("Bandit")
    a.stats['Attack'] = 999
    assert b.stats['Attack'] != 999


def test_enemy_hp_and_alive():
    e = Enemy("Bandit")
    assert e.hp == e.max_hp > 0
    assert e.is_alive()
    e.hp = 0
    assert not e.is_alive()


# --- Combat with a group ------------------------------------------------------------------

def test_group_spawns_the_requested_number_of_enemies():
    combat = make_group_combat(3)
    assert len(combat.enemies) == 3
    assert all(e.name == "Bandit" for e in combat.enemies)


def test_turn_order_includes_the_player_and_every_enemy():
    combat = make_group_combat(3)
    kinds = [kind for kind, _ in combat.turn_order]
    assert kinds.count("player") == 1
    assert kinds.count("enemy") == 3


def test_victory_requires_every_enemy_defeated():
    combat = make_group_combat(2)
    combat.enemies[0].hp = 0
    assert any(e.is_alive() for e in combat.enemies)  # one still standing -> not over yet
    combat.enemies[1].hp = 0
    assert not any(e.is_alive() for e in combat.enemies)


def test_choose_target_auto_picks_the_lone_survivor():
    combat = make_group_combat(3)
    combat.enemies[0].hp = 0
    combat.enemies[1].hp = 0
    assert combat._choose_target() == 2


def test_choose_target_prompts_when_multiple_are_alive(monkeypatch):
    combat = make_group_combat(3)
    monkeypatch.setattr("builtins.input", lambda *_: "2")
    assert combat._choose_target() == 1  # "2" -> index 1


def test_choose_target_rejects_a_dead_enemys_number_and_retries(monkeypatch):
    combat = make_group_combat(3)
    combat.enemies[0].hp = 0
    inputs = iter(["1", "2"])  # "1" is dead, should be rejected; "2" is valid
    monkeypatch.setattr("builtins.input", lambda *_: next(inputs))
    assert combat._choose_target() == 1


def test_player_attack_never_touches_untargeted_enemies(monkeypatch):
    # Intelligence 0 -> confusion can never trigger, so a single-target attack should never
    # touch the other two enemies, hit or miss.
    for _ in range(30):
        combat = make_group_combat(3)
        monkeypatch.setattr("builtins.input", lambda *_: "1")
        combat.player_attack(is_magic_attack=False)
        assert combat.enemies[1].hp == combat.enemies[1].max_hp
        assert combat.enemies[2].hp == combat.enemies[2].max_hp


def test_confusion_redirect_still_results_in_a_miss(monkeypatch):
    # Known limitation: confusion changes which enemy's name is printed, but the underlying
    # damage from calculate_player_damage is unconditionally 0 on confusion, so a redirect
    # never actually deals damage to the new target either — it's flavor text, not a real hit.
    pd = PlayerData(name="T", role="warrior", level=1, hp=999,
                     stats={'Strength': 5, 'Agility': 5, 'Intelligence': -100, 'Defence': 5,
                            'Magic': 5, 'Luck': 5}, max_hp=999)
    combat = Combat(pd, "Bandit", group_size=3)
    monkeypatch.setattr("builtins.input", lambda *_: "1")
    monkeypatch.setattr("random.random", lambda: 0.0)  # guarantees confusion (chance is 35%)
    hp_before = [e.hp for e in combat.enemies]

    result = combat.player_attack(is_magic_attack=False)

    assert result is False
    assert [e.hp for e in combat.enemies] == hp_before


def test_bomb_hits_every_alive_enemy(monkeypatch):
    # Bandit's max HP (20) is below 35, so damage floors at 0 rather than going negative
    combat = make_group_combat(3)
    combat.player.loot = ["Bomb"]
    monkeypatch.setattr("builtins.input", lambda *_: "1")
    before = [e.hp for e in combat.enemies]
    combat.use_item()
    after = [e.hp for e in combat.enemies]
    assert all(a == max(0, b - 35) for b, a in zip(before, after))


def test_bomb_skips_already_dead_enemies(monkeypatch):
    combat = make_group_combat(3)
    combat.enemies[0].hp = 0
    combat.player.loot = ["Bomb"]
    monkeypatch.setattr("builtins.input", lambda *_: "1")
    combat.use_item()
    assert combat.enemies[0].hp == 0
    assert combat.enemies[1].hp == max(0, combat.enemies[1].max_hp - 35)
    assert combat.enemies[2].hp == max(0, combat.enemies[2].max_hp - 35)


def test_debuff_only_affects_the_target_not_its_siblings(monkeypatch):
    combat = make_group_combat(3, enemy="Bandit")
    target = combat.enemies[0]
    sibling = combat.enemies[1]
    monkeypatch.setattr("random.choice", lambda seq: seq[0])
    before_target = dict(target.stats)
    before_sibling = dict(sibling.stats)

    combat.apply_debuff_to_enemy(target, 5)

    assert target.stats != before_target
    assert sibling.stats == before_sibling


def test_corruption_ticks_only_for_the_acting_enemy():
    combat = make_group_combat(2, enemy="Jester")  # Jester has Corruption 20
    combat.current_turn = "enemy"
    combat.current_enemy_index = 0

    combat.enemy_turn()

    assert combat.enemies[0].corruption_counter > 0
    assert combat.enemies[1].corruption_counter == 0
    assert combat.enemies[1].hp == combat.enemies[1].max_hp


def test_full_group_fight_ends_in_victory_for_an_overwhelming_player(monkeypatch):
    pd = PlayerData(name="T", role="warrior", level=1, hp=9999,
                     stats={'Strength': 50, 'Agility': 50, 'Intelligence': 0, 'Defence': 50,
                            'Magic': 0, 'Luck': 0}, max_hp=9999)
    combat = Combat(pd, "Bandit", group_size=2)
    combat.player.current_hp = 9999
    monkeypatch.setattr("builtins.input", lambda *_: "1")  # attack; and "1" targets whoever's first if asked

    result, hp = combat.run_combat()

    assert result == "victory"
    assert all(not e.is_alive() for e in combat.enemies)


# --- pyrpg.py: rewards are summed per enemy, not a single roll * group_size ---------------

def test_group_victory_calls_reward_calculations_once_per_enemy(monkeypatch):
    from game.pyrpg import PYRPG
    game = PYRPG.__new__(PYRPG)
    game.player_data = PlayerData(name="T", role="warrior", level=1, hp=30, stats=dict(STATS), max_hp=30)

    monkeypatch.setattr("game.pyrpg.get_encounter_enemy", lambda power: "Bandit")
    monkeypatch.setattr("game.pyrpg.roll_group_size", lambda: 3)
    monkeypatch.setattr("game.pyrpg.start_combat", lambda player_data, enemy_name, group_size: ("victory", 30))
    monkeypatch.setattr(game, "auto_save_player_state", lambda: None)
    monkeypatch.setattr(game, "_process_level_ups", lambda: None)
    monkeypatch.setattr("builtins.input", lambda *_: "")

    gold_calls = []
    exp_calls = []
    loot_calls = []
    monkeypatch.setattr(game, "calculate_gold_reward", lambda: gold_calls.append(1) or 10)
    monkeypatch.setattr(game, "calculate_exp_reward", lambda enemy_name: exp_calls.append(1) or 5)
    monkeypatch.setattr(game, "_roll_for_loot", lambda: loot_calls.append(1))

    game.enter_combat()

    assert len(gold_calls) == 3
    assert len(exp_calls) == 3
    assert len(loot_calls) == 3
    assert game.player_data.gold == 30
    assert game.player_data.exp == 15


def test_solo_victory_still_calls_reward_calculations_exactly_once(monkeypatch):
    from game.pyrpg import PYRPG
    game = PYRPG.__new__(PYRPG)
    game.player_data = PlayerData(name="T", role="warrior", level=1, hp=30, stats=dict(STATS), max_hp=30)

    monkeypatch.setattr("game.pyrpg.get_encounter_enemy", lambda power: "Bandit")
    monkeypatch.setattr("game.pyrpg.roll_group_size", lambda: 1)
    monkeypatch.setattr("game.pyrpg.start_combat", lambda player_data, enemy_name, group_size: ("victory", 30))
    monkeypatch.setattr(game, "auto_save_player_state", lambda: None)
    monkeypatch.setattr(game, "_process_level_ups", lambda: None)
    monkeypatch.setattr("builtins.input", lambda *_: "")

    gold_calls = []
    monkeypatch.setattr(game, "calculate_gold_reward", lambda: gold_calls.append(1) or 10)
    monkeypatch.setattr(game, "calculate_exp_reward", lambda enemy_name: 5)
    monkeypatch.setattr(game, "_roll_for_loot", lambda: None)

    game.enter_combat()

    assert len(gold_calls) == 1
    assert game.player_data.gold == 10
