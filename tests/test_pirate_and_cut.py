"""v1.0.6 abilities: Pirate's Rum and Flintlock, and the Cut learning item"""
from combat.combat import Combat, start_combat
from combat.damage_calculator import DamageCalculator
from game.pyrpg import PYRPG
from players.player_data import PlayerData
from spells.spells_data import learning_item_spell, level_up_spells, uses_per_combat

PIRATE = {'Strength': 2, 'Agility': 5, 'Intelligence': -8, 'Charisma': -4, 'Defense': 6, 'Magic': 0, 'Luck': 11}


def pirate(**overrides):
    defaults = dict(name="P", role="pirate", level=3, hp=10, stats=dict(PIRATE), max_hp=22,
                    known_spells=["Rum", "Flintlock"], in_town=False, distance=1)
    defaults.update(overrides)
    return PlayerData(**defaults)


def replies(monkeypatch, *answers):
    it = iter(answers)
    monkeypatch.setattr("builtins.input", lambda *_: next(it, "1"))


# --- learning --------------------------------------------------------------------------------

def test_pirates_start_with_rum_and_learn_to_shoot_at_level_3():
    assert level_up_spells("pirate", 1) == ["Rum"]
    assert level_up_spells("pirate", 2) == ["Rum"]
    assert level_up_spells("pirate", 3) == ["Rum", "Flintlock"]


def test_a_new_pirate_knows_rum():
    game = PYRPG.__new__(PYRPG)
    game.player_data = pirate(level=1, known_spells=[])
    game._learn_level_up_spells()
    assert game.player_data.known_spells == ["Rum"]


def test_limits():
    assert uses_per_combat("Rum") == 2
    assert uses_per_combat("Flintlock") == 1
    assert uses_per_combat("Hyper beam") == 1
    assert uses_per_combat("Cut") is None


# --- Rum ------------------------------------------------------------------------------------

def test_rum_formulas():
    assert DamageCalculator.rum_heal(PIRATE) == int(11 * 0.25 + 8)      # 10
    assert DamageCalculator.rum_heal({'Luck': 0, 'Intelligence': 0}) == 5
    assert DamageCalculator.rum_int_loss(-8) == 8
    assert DamageCalculator.rum_int_loss(-40) == 18


def test_rum_heals_then_the_second_swig_hits_harder(capsys):
    combat = Combat(pirate(hp=1, max_hp=22), "Weakling")
    max_hp = combat.player.max_hp
    combat.cast("Rum")
    assert combat.player.current_hp == min(max_hp, 1 + 10)
    assert combat.player.stats["Intelligence"] == -16
    combat.player.current_hp = 1
    combat.cast("Rum")
    assert combat.player.current_hp == min(max_hp, 1 + int(11 * 0.25 + 16))  # 18
    assert combat.player.stats["Intelligence"] == -24


def test_rum_only_twice_a_fight():
    combat = Combat(pirate(), "Weakling")
    assert combat.cast("Rum") == "end_turn"
    assert combat.cast("Rum") == "end_turn"
    assert combat.cast("Rum") is None
    assert combat._cost_label("Rum") == "used up this fight"


def test_rum_is_free_and_never_wastes_mana(monkeypatch):
    combat = Combat(pirate(mana=0), "Weakling")
    monkeypatch.setattr(Combat, "_rolled_waste", lambda self: (_ for _ in ()).throw(AssertionError("rolled")))
    assert combat.cast("Rum") == "end_turn"
    assert combat._cost_label("Rum") == "1/2 left this fight"


def test_the_hangover_doesnt_last_past_the_fight(monkeypatch):
    pd = pirate()
    replies(monkeypatch, "2", "1")          # Spells & Abilities -> Rum, then attack until it's over
    start_combat(pd, "Weakling")
    assert pd.stats["Intelligence"] == -8


# --- Flintlock ------------------------------------------------------------------------------

def test_flintlock_damage_and_coin_formulas():
    assert DamageCalculator.ability_damage("Flintlock", PIRATE) == int(18 + 16 * 0.85)   # 31
    assert DamageCalculator.flintlock_gold_chance(11) == 11 * 0.8
    assert DamageCalculator.flintlock_gold(11) == 8
    assert DamageCalculator.flintlock_gold(1) == 3
    assert DamageCalculator.flintlock_gold(100) == 12


def test_flintlock_fires_once_a_fight(monkeypatch):
    combat = Combat(pirate(), "Troll")
    replies(monkeypatch, "1")
    assert combat.cast("Flintlock") == "end_turn"
    assert combat.cast("Flintlock") is None


def test_flintlock_coins_are_paid_out_on_a_win(monkeypatch):
    pd = pirate(gold=0)
    monkeypatch.setattr("combat.combat.random.uniform", lambda a, b: 0)     # the coin proc always hits
    replies(monkeypatch, "2", "2", "1")       # Spells & Abilities -> Flintlock -> target 1
    result, *_ = start_combat(pd, "Weakling")
    assert result == "victory" and pd.gold == 8


def test_no_coins_without_the_proc(monkeypatch):
    pd = pirate(gold=0)
    monkeypatch.setattr("combat.combat.random.uniform", lambda a, b: 99.9)
    replies(monkeypatch, "2", "2", "1")
    start_combat(pd, "Weakling")
    assert pd.gold == 0


# --- Cut ------------------------------------------------------------------------------------

def test_hm01_is_a_shop_item_that_teaches_cut():
    from items.items_data import is_item_buyable, is_item_consumable, is_item_droppable, get_item_rarity
    assert learning_item_spell("HM01") == "Cut"
    assert is_item_buyable("HM01") and is_item_consumable("HM01") and not is_item_droppable("HM01")
    assert get_item_rarity("HM01") == 8


def test_cut_damage_takes_the_best_of_luck_agility_and_strength():
    assert DamageCalculator.ability_damage("Cut", PIRATE) == 3
    assert DamageCalculator.ability_damage("Cut", {'Luck': 0, 'Agility': -40, 'Strength': 20}) == 8


def test_cut_sears_through_any_defense(monkeypatch):
    combat = Combat(pirate(known_spells=["Cut"]), "Living armor")         # Defense 100
    replies(monkeypatch, "1")
    hp = combat.enemies[0].hp
    combat.cast("Cut")
    assert combat.enemies[0].hp == hp - 3


def test_learning_cut_from_hm01():
    game = PYRPG.__new__(PYRPG)
    game.player_data = pirate(known_spells=[], loot=["HM01"])
    assert game.use_item_outside_combat("HM01")
    assert "Cut" in game.player_data.known_spells and game.player_data.loot == []
