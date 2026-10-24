import random

from combat.combat import Combat
from combat.damage_calculator import DamageCalculator
from game.pyrpg import PYRPG
from players.player_data import PlayerData
from roles.roles_data import RolesExtract
from spells.spells_data import STARTING_ITEMS, can_learn, spell_cost, spell_base_damage

MAGE = {'Strength': 3, 'Agility': 4, 'Intelligence': 10, 'Defence': 3, 'Magic': 9, 'Luck': 5}   # 45 max mana
NECRO = {'Strength': 1, 'Agility': 2, 'Intelligence': 6, 'Defence': 4, 'Magic': -8, 'Luck': 5}  # 27 max mana


def make_combat(stats, enemy="Bandit", size=1, **overrides):
    defaults = dict(name="T", role="mage", level=1, hp=99, stats=dict(stats), max_hp=99)
    defaults.update(overrides)
    return Combat(PlayerData(**defaults), enemy, group_size=size)


def answer(monkeypatch, *responses):
    replies = iter(responses)
    monkeypatch.setattr("builtins.input", lambda *_: next(replies, "1"))


def no_waste(monkeypatch):
    monkeypatch.setattr("combat.combat.random.randint", lambda a, b: b)  # rolls high -> no waste/debuff


# --- the spells menu ---------------------------------------------------------------------------

def test_no_spells_means_nothing_to_cast_and_the_turn_is_kept(monkeypatch):
    combat = make_combat(MAGE)
    answer(monkeypatch)
    assert combat.cast_menu() is None


def test_cursed_spells_only_show_for_negative_magic():
    assert make_combat(MAGE, known_spells=["DOOM"]).available_spells() == []
    assert make_combat(NECRO, known_spells=["DOOM"]).available_spells() == ["DOOM"]


def test_hyper_beam_is_granted_only_while_the_beam_staff_is_worn():
    assert "Hyper beam" not in make_combat(MAGE).available_spells()
    assert "Hyper beam" in make_combat(MAGE, equipped="Beam staff").available_spells()


# --- paying for spells -------------------------------------------------------------------------

def test_mana_surge_costs_and_hits_harder_every_cast(monkeypatch):
    assert [spell_cost("Mana surge", n) for n in range(3)] == [5, 8, 11]
    assert [spell_base_damage("Mana surge", n) for n in range(3)] == [2, 4, 6]

    no_waste(monkeypatch)
    combat = make_combat(MAGE, known_spells=["Mana surge"])
    combat.cast("Mana surge")
    combat.cast("Mana surge")
    assert combat.player.current_mana == 45 - 5 - 8


def test_cannot_cast_without_enough_mana(monkeypatch):
    no_waste(monkeypatch)
    combat = make_combat(MAGE, known_spells=["Mana surge"], mana=4)
    assert combat.cast("Mana surge") is None
    assert combat.player.current_mana == 4


def test_negative_intelligence_can_waste_1_5x_mana_but_the_spell_still_fires(monkeypatch):
    monkeypatch.setattr("combat.combat.random.randint", lambda a, b: 1)  # waste always triggers
    stats = {**MAGE, 'Intelligence': -10}  # max mana 45
    combat = make_combat(stats, known_spells=["Mana surge"])
    hp_before = combat.enemies[0].hp
    combat.cast("Mana surge")
    assert combat.player.current_mana == 45 - 7  # int(5 * 1.5)
    assert combat.enemies[0].hp < hp_before


def test_wasted_cost_above_your_mana_just_drains_it(monkeypatch):
    monkeypatch.setattr("combat.combat.random.randint", lambda a, b: 1)
    combat = make_combat({**MAGE, 'Intelligence': -10}, known_spells=["Mana surge"], mana=6)
    combat.cast("Mana surge")
    assert combat.player.current_mana == 0


def test_cursed_spells_cost_hp_not_mana(monkeypatch):
    no_waste(monkeypatch)
    combat = make_combat(NECRO, known_spells=["DOOM"])
    mana_before, hp_before = combat.player.current_mana, combat.player.current_hp
    combat.cast("DOOM")
    assert combat.player.current_mana == mana_before
    assert combat.player.current_hp == hp_before - round(min(8, 8 * 0.88))


def test_cursed_spell_you_cant_pay_for_kills_you(monkeypatch):
    no_waste(monkeypatch)
    combat = make_combat(NECRO, known_spells=["DOOM"], hp=3)
    combat.cast("DOOM")
    assert not combat.player.is_alive()
    assert combat.combat_ongoing is False


def test_hyper_beam_spends_all_mana_and_only_once_per_fight(monkeypatch):
    no_waste(monkeypatch)
    combat = make_combat(MAGE, equipped="Beam staff", enemy="Dragon")
    combat.cast("Hyper beam")
    assert combat.player.current_mana == 0
    assert combat.cast("Hyper beam") is None


# --- damage formulas ---------------------------------------------------------------------------

def test_spell_multiplier_normal_vs_cursed():
    assert round(DamageCalculator.spell_multiplier(9), 2) == 1.9
    assert round(DamageCalculator.spell_multiplier(-8), 2) == 0.2          # normal spell, -Magic: weak
    assert round(DamageCalculator.spell_multiplier(-8, cursed=True), 2) == 1.8
    assert DamageCalculator.spell_multiplier(-50) == 0.1         # floored


def test_intelligence_spell_bonus():
    # int(0.5 * 10) + int(min(6 // 3, 9 * 0.8)) = 5 + 2
    assert DamageCalculator.intelligence_spell_bonus(10, -6, 9) == 7
    assert DamageCalculator.intelligence_spell_bonus(10, 6, 9) == 0


def test_mana_waste_chance():
    assert DamageCalculator.mana_waste_chance(-2) == 7
    assert DamageCalculator.mana_waste_chance(-50) == 35
    assert DamageCalculator.mana_waste_chance(5) == 0


# --- abilities ---------------------------------------------------------------------------------

def test_blade_rush_channels_for_4_turns_hitting_everyone(monkeypatch):
    no_waste(monkeypatch)
    combat = make_combat(MAGE, enemy="Dragon", size=2, known_spells=["Blade rush"])
    combat.cast("Blade rush")
    assert combat.channel["turns_left"] == 3
    for _ in range(3):
        combat._continue_channel()
    assert combat.channel is None
    assert all(e.hp < e.max_hp for e in combat.enemies)


def test_natures_gift_heals_5_for_3_turns(monkeypatch):
    no_waste(monkeypatch)
    combat = make_combat(MAGE, known_spells=["Nature's gift"])
    combat.player.current_hp = 5                 # max HP is 22
    combat.cast("Nature's gift")
    combat._tick_heal_over_time()
    combat._tick_heal_over_time()
    combat._tick_heal_over_time()  # no 4th tick
    assert combat.player.current_hp == 20


# --- learning ----------------------------------------------------------------------------------

def make_game(stats, **overrides):
    game = PYRPG.__new__(PYRPG)
    defaults = dict(name="T", role="mage", level=1, hp=30, stats=dict(stats), max_hp=30)
    defaults.update(overrides)
    game.player_data = PlayerData(**defaults)
    return game


def test_using_a_book_learns_the_spell_and_uses_the_book_up():
    game = make_game(MAGE, loot=["Mana surge book"])
    assert game.use_item_outside_combat("Mana surge book") is True
    assert game.player_data.known_spells == ["Mana surge"]
    assert game.player_data.loot == []


def test_a_known_spell_cant_be_learned_twice():
    game = make_game(MAGE, loot=["Mana surge book"], known_spells=["Mana surge"])
    assert game.use_item_outside_combat("Mana surge book") is False
    assert game.player_data.loot == ["Mana surge book"]


def test_positive_magic_cant_learn_cursed_spells():
    assert can_learn("DOOM", -1) and not can_learn("DOOM", 0)
    game = make_game(MAGE, loot=["Scroll of doom"])
    assert game.use_item_outside_combat("Scroll of doom") is False
    assert game.player_data.known_spells == []


def test_starting_items_belong_to_real_roles():
    roles = {role.lower() for role in RolesExtract.get_role_stats_by_name()}
    assert set(STARTING_ITEMS) <= roles


# --- level-up learning (Cursed strike) ---------------------------------------------------------

FORSAKEN = {'Strength': -1, 'Agility': 4, 'Intelligence': 2, 'Defence': 10, 'Magic': -4, 'Luck': 4}


def test_forsaken_learns_cursed_strike_on_reaching_level_2(monkeypatch):
    game = make_game(FORSAKEN, role="forsaken", exp=100)
    monkeypatch.setattr(game, "_allocate_level_up_points", lambda points: None)
    game._process_level_ups()
    assert game.player_data.level == 2
    assert game.player_data.known_spells == ["Cursed strike"]


def test_level_1_forsaken_doesnt_know_it_yet_and_it_isnt_learned_twice():
    game = make_game(FORSAKEN, role="forsaken")
    game._learn_level_up_spells()
    assert game.player_data.known_spells == []
    game.player_data.level = 5
    game._learn_level_up_spells()
    game._learn_level_up_spells()
    assert game.player_data.known_spells == ["Cursed strike"]


def test_a_forsaken_who_raised_magic_to_positive_cant_learn_it():
    game = make_game({**FORSAKEN, 'Magic': 1}, role="forsaken", level=2)
    game._learn_level_up_spells()
    assert game.player_data.known_spells == []


def test_cursed_strike_costs_3_hp_and_hits_for_3_times_the_cursed_multiplier(monkeypatch):
    no_waste(monkeypatch)
    combat = make_combat(FORSAKEN, enemy="Dragon", known_spells=["Cursed strike"])
    hp_before, dragon_before = combat.player.current_hp, combat.enemies[0].hp
    combat.cast("Cursed strike")
    assert combat.player.current_hp == hp_before - 3              # round(min(4, 3 * 0.88))
    assert combat.enemies[0].hp < dragon_before
