"""v1.0.6 passive encounters: the roll, chests & Mimics, the Cook, Graveyard, Sudden Hunger, Halt!"""
import pytest

from adventures import encounters
from adventures.adventures import graveyard, halt, sudden_hunger
from adventures.encounters import (chest, cook, eligible, is_bad, meets, notice_chance, parse_range,
                                   roll_town_encounter, roll_wild_encounter, weight)
from combat.combat import Combat, Enemy
from game.pyrpg import PYRPG
from players.player_data import PlayerData
from util.charisma import charisma_range, odds_sway_percent

STATS = {'Strength': 5, 'Agility': 5, 'Intelligence': 0, 'Charisma': 0, 'Defense': 5, 'Magic': 5, 'Luck': 5}
CHEST = {"Type": "Chest", "Description": "Chest", "Depth": "1", "Odds": "25", "Enemy_spawn": ""}
MIMIC = {"Type": "Chest", "Description": "Mimic", "Depth": "1", "Odds": "5", "Enemy_spawn": "Mimic"}
COOK = {"Type": "Healer", "Description": "Cook", "Depth": "5", "Odds": "22", "Cost": "v*1.5~2.3",
        "Charisma_effect": "yes"}
HALT = {"Type": "Event", "Description": "Halt!", "Depth": "town", "Odds": "5", "Cost": "0/15~40",
        "Enemy_spawn": "Guard *1", "Charisma_effect": "yes", "Charisma_req": "<0"}
HUNGER = {"Type": "Event", "Description": "Sudden Hunger", "Depth": "6", "Value": "+=11", "Odds": "15",
          "Enemy_spawn": "slime", "HP_req": "<=50%"}
GRAVEYARD = {"Type": "Adventure", "Description": "Graveyard", "Depth": "6", "Odds": "8", "Enemy_spawn": "Zombie *3"}
CURSE = {"Type": "Curse", "Description": "Of fear", "Depth": "5", "Odds": "1.5"}


def make_game(charisma=0, intelligence=0, **overrides):
    game = PYRPG.__new__(PYRPG)
    stats = dict(STATS, Charisma=charisma, Intelligence=intelligence)
    defaults = dict(name="T", role="warrior", level=1, hp=40, stats=stats, max_hp=40, gold=100,
                    in_town=False, distance=10)
    defaults.update(overrides)
    game.player_data = PlayerData(**defaults)
    return game


def replies(monkeypatch, *answers):
    it = iter(answers)
    monkeypatch.setattr("builtins.input", lambda *_: next(it, ""))


def record_fights(monkeypatch, result="victory"):
    fights = []

    def fake_fight(self, enemy, size=1, surprise=False, scaling=0, on_victory=None):
        fights.append({"enemy": enemy, "size": size, "surprise": surprise, "scaling": scaling})
        if result == "victory" and on_victory:
            on_victory()
        return result
    monkeypatch.setattr(PYRPG, "fight", fake_fight)
    return fights


@pytest.fixture(autouse=True)
def quiet_impressions(monkeypatch):
    """No gut feelings unless a test asks for them"""
    monkeypatch.setattr(encounters, "FINE_FLAVOR_CHANCE", 0)


# --- requirements and odds -----------------------------------------------------------------------

def test_requirements():
    assert meets("", 5)
    assert meets("<0", -1) and not meets("<0", 0)
    assert meets("<=50%", 20, 40) and not meets("<=50%", 21, 40)
    assert meets(">=5", 5)


def test_depth_and_town_rows():
    assert not eligible(make_game(distance=4), COOK)
    assert eligible(make_game(distance=5), COOK)
    assert not eligible(make_game(charisma=-5), HALT)                   # town rows never out there
    assert eligible(make_game(charisma=-5), HALT, in_town=True)
    assert not eligible(make_game(charisma=0), HALT, in_town=True)      # Halt! is -Charisma only


def test_sudden_hunger_needs_half_hp_or_less():
    assert not eligible(make_game(hp=21, distance=6), HUNGER)
    assert eligible(make_game(hp=20, distance=6), HUNGER)


def test_only_disguised_and_cursed_rows_are_bad():
    assert is_bad(MIMIC) and is_bad(CURSE)
    assert not is_bad(CHEST) and not is_bad(COOK)


def test_charisma_sways_bad_odds_both_ways():
    assert odds_sway_percent(40) == 10
    assert weight(MIMIC, 40) == pytest.approx(4.5)
    assert weight(MIMIC, -40) == pytest.approx(5.5)
    assert weight(CHEST, -40) == 25
    assert odds_sway_percent(500) == 20


def test_a_quarter_of_explores_are_passive(monkeypatch):
    game = make_game()
    monkeypatch.setattr(encounters, "get_encounters", lambda: [CHEST])
    monkeypatch.setattr("adventures.encounters.random.randint", lambda a, b: 26)
    assert roll_wild_encounter(game) is None
    monkeypatch.setattr("adventures.encounters.random.randint", lambda a, b: 25)
    assert roll_wild_encounter(game) is CHEST


def test_unbuilt_encounter_types_are_never_rolled(monkeypatch):
    game = make_game()
    merchant = {"Type": "SomethingNew", "Description": "?", "Depth": "1", "Odds": "99"}
    monkeypatch.setattr(encounters, "get_encounters", lambda: [merchant])
    monkeypatch.setattr("adventures.encounters.random.randint", lambda a, b: 1)
    assert roll_wild_encounter(game) is None


def test_every_wild_row_in_the_csv_reads(monkeypatch):
    """The real CSV: every requirement parses, every row at depth 100 can be checked"""
    game = make_game(distance=100, hp=10)
    for row in encounters.get_encounters():
        eligible(game, row)
        eligible(game, row, in_town=True)
        weight(row, -50)


def test_explore_runs_the_encounter_instead_of_a_fight(monkeypatch):
    game = make_game()
    ran = []
    monkeypatch.setattr("adventures.encounters.roll_wild_encounter", lambda g: CHEST)
    monkeypatch.setattr("adventures.encounters.run_encounter", lambda g, row: ran.append(row))
    monkeypatch.setattr(PYRPG, "enter_combat", lambda self: (_ for _ in ()).throw(AssertionError("fought")))
    game.explore()
    assert ran == [CHEST]


# --- Intelligence noticing ---------------------------------------------------------------------

def test_notice_chance():
    assert notice_chance(-5) == 0
    assert notice_chance(10) == 17
    assert notice_chance(100) == 45


def test_a_sharp_mind_can_see_a_mimic(monkeypatch, capsys):
    game = make_game(intelligence=30)
    monkeypatch.setattr("adventures.encounters.random.randint", lambda a, b: 1)
    replies(monkeypatch, "n")
    chest(game, MIMIC)
    line = capsys.readouterr().out
    assert any(flavor in line for flavor in encounters.NOTICE_FLAVOR["Chest"])


def test_a_real_chest_is_never_noticed_as_bad(monkeypatch, capsys):
    game = make_game(intelligence=30)
    monkeypatch.setattr("adventures.encounters.random.randint", lambda a, b: 1)
    replies(monkeypatch, "n")
    chest(game, CHEST)
    assert not any(flavor in capsys.readouterr().out for flavor in encounters.NOTICE_FLAVOR["Chest"])


# --- chests and Mimics -----------------------------------------------------------------------------

def test_a_real_chest_pays_out(monkeypatch):
    game = make_game(gold=0)
    record_fights(monkeypatch)
    monkeypatch.setattr(PYRPG, "_roll_for_loot", lambda self, source: None)
    replies(monkeypatch, "y")
    assert chest(game, CHEST) == "chest"
    assert 5 <= game.player_data.gold <= 13


def test_leaving_a_chest_alone(monkeypatch):
    game = make_game(gold=0)
    fights = record_fights(monkeypatch)
    replies(monkeypatch, "n")
    assert chest(game, MIMIC) is None
    assert fights == [] and game.player_data.gold == 0


def test_a_mimic_surprise_attacks_scaled_to_depth_and_pays_bonus_gold(monkeypatch):
    game = make_game(gold=0, distance=10)
    fights = record_fights(monkeypatch)
    replies(monkeypatch, "y")
    assert chest(game, MIMIC) == "victory"
    assert fights == [{"enemy": "Mimic", "size": 1, "surprise": True, "scaling": 9}]
    assert 3 <= game.player_data.gold <= 11


def test_mimic_scaling_adds_to_positive_stats_and_includes_the_depth_50_buff():
    shallow = Enemy("Mimic", depth=10, scaling=9)
    assert (shallow.stats["HP"], shallow.stats["Attack"], shallow.stats["Luck"]) == (29, 14, 0)
    deep = Enemy("Mimic", depth=60, scaling=59)
    assert deep.stats["HP"] == 20 + 59 + 10


def test_mimics_and_guards_never_show_up_as_random_fights():
    from enemies.enemies_data import get_encounter_weights
    names = {name.lower() for name, _ in get_encounter_weights(50)}
    assert "mimic" not in names and "guard" not in names


def test_a_surprise_attack_puts_every_enemy_first(monkeypatch):
    pd = make_game(stats=dict(STATS, Agility=200)).player_data
    combat = Combat(pd, "Wolf", 2, surprise=True)
    assert [kind for kind, _ in combat.turn_order] == ["enemy", "enemy", "player"]


# --- the Cook ---------------------------------------------------------------------------------

def test_charisma_range():
    assert charisma_range(1.5, 2.3, 0) == pytest.approx(1.9)
    assert charisma_range(1.5, 2.3, 100) == pytest.approx(1.5)
    assert charisma_range(1.5, 2.3, -100) == pytest.approx(2.3)
    assert charisma_range(15, 40, -1, ugly_only=True) == 15
    assert charisma_range(15, 40, -100, ugly_only=True) == 40


def test_parse_range():
    assert parse_range("v*1.5~2.3") == (1.5, 2.3)
    assert parse_range("0/15~40") == (15, 40)


def test_the_cook_heals_what_you_pay_for(monkeypatch):
    game = make_game(hp=10, max_hp=40, gold=100)           # 0 Charisma: 1.9 gold per HP
    replies(monkeypatch, "10", "")
    assert cook(game, COOK) == 10
    assert game.player_data.hp == 20
    assert game.player_data.gold == 100 - 19


def test_a_pretty_face_eats_cheaper(monkeypatch):
    game = make_game(charisma=100, hp=10, max_hp=40, gold=100)
    replies(monkeypatch, "10", "")
    cook(game, COOK)
    assert game.player_data.gold == 100 - 15


def test_the_cook_never_sells_more_than_you_can_pay_or_need(monkeypatch):
    game = make_game(hp=10, max_hp=40, gold=10)             # 10 gold / 1.9 = 5 HP at most
    replies(monkeypatch, "6", "")
    assert cook(game, COOK) == 0
    assert game.player_data.gold == 10 and game.player_data.hp == 10


# --- Graveyard and Sudden Hunger -----------------------------------------------------------------

def test_the_graveyard_wakes_the_dead_then_gives_a_chest(monkeypatch):
    game = make_game(gold=0)
    fights = record_fights(monkeypatch)
    monkeypatch.setattr(PYRPG, "_roll_for_loot", lambda self, source: None)
    replies(monkeypatch, "y")
    assert graveyard(game, GRAVEYARD) == "victory"
    assert fights[0]["enemy"] == "Zombie" and fights[0]["size"] == 3
    assert 5 <= game.player_data.gold <= 13


def test_losing_at_the_graveyard_gives_no_chest(monkeypatch):
    game = make_game(gold=0)
    record_fights(monkeypatch, result="defeat")
    replies(monkeypatch, "y")
    graveyard(game, GRAVEYARD)
    assert game.player_data.gold == 0


def test_sudden_hunger_heals_then_the_owner_shows_up(monkeypatch):
    game = make_game(hp=15, max_hp=40, distance=6)
    fights = record_fights(monkeypatch)
    replies(monkeypatch, "y")
    sudden_hunger(game, HUNGER)
    assert game.player_data.hp == 26
    assert fights[0]["enemy"] == "Slime"


def test_not_eating_is_safe(monkeypatch):
    game = make_game(hp=15, distance=6)
    fights = record_fights(monkeypatch)
    replies(monkeypatch, "n")
    assert sudden_hunger(game, HUNGER) is None
    assert fights == [] and game.player_data.hp == 15


# --- Halt! ---------------------------------------------------------------------------------------

def test_halt_only_stops_the_ugly_on_the_way_back(monkeypatch):
    monkeypatch.setattr(encounters, "get_encounters", lambda: [HALT])
    monkeypatch.setattr("adventures.encounters.random.uniform", lambda a, b: 4.9)
    assert roll_town_encounter(make_game(charisma=-1, in_town=True)) is HALT
    assert roll_town_encounter(make_game(charisma=0, in_town=True)) is None
    monkeypatch.setattr("adventures.encounters.random.uniform", lambda a, b: 5.0)
    assert roll_town_encounter(make_game(charisma=-1, in_town=True)) is None


def test_paying_the_fine(monkeypatch):
    game = make_game(charisma=-1, gold=100)
    fights = record_fights(monkeypatch)
    replies(monkeypatch, "1", "")
    assert halt(game, HALT) == "paid"
    assert game.player_data.gold == 85 and fights == []


def test_the_uglier_the_bigger_the_fine(monkeypatch):
    game = make_game(charisma=-50, gold=100)
    replies(monkeypatch, "1", "")
    halt(game, HALT)
    assert game.player_data.gold == 60


def test_refusing_and_losing_costs_the_full_fine(monkeypatch):
    game = make_game(charisma=-1, gold=100)
    fights = record_fights(monkeypatch, result="defeat")
    replies(monkeypatch, "2", "")
    assert halt(game, HALT) == "defeat"
    assert fights[0]["enemy"] == "Guard"
    assert game.player_data.gold == 60


def test_too_broke_to_pay_means_a_fight_and_the_guard_takes_it_all(monkeypatch):
    game = make_game(charisma=-1, gold=10)
    fights = record_fights(monkeypatch, result="defeat")
    replies(monkeypatch, "1", "")
    halt(game, HALT)
    assert len(fights) == 1 and game.player_data.gold == 0


def test_winning_against_the_guard_keeps_your_gold(monkeypatch):
    game = make_game(charisma=-1, gold=100)
    record_fights(monkeypatch)
    replies(monkeypatch, "2", "")
    assert halt(game, HALT) == "victory"
    assert game.player_data.gold == 100


def test_returning_to_town_can_be_halted(monkeypatch):
    game = make_game(charisma=-5, distance=1)
    halted = []
    monkeypatch.setattr("game.pyrpg.random.randint", lambda a, b: 1)
    monkeypatch.setattr("adventures.encounters.roll_town_encounter", lambda g: HALT)
    monkeypatch.setattr("adventures.encounters.run_encounter", lambda g, row: halted.append(g.player_data.in_town))
    game.return_to_town()
    assert halted == [True]     # you're already back in town when the guard steps up


# --- wandering merchants and thieves -------------------------------------------------------------

from adventures.encounters import merchant, merchant_stock, sell_price

MERCHANT = {"Type": "Merchant", "Description": "Merchant", "Depth": "11", "Cost": "*=1.3", "Odds": "25",
            "Enemy_spawn": "", "Charisma_effect": "no"}
THIEF = dict(MERCHANT, Description="Thief merchant", Odds="11", Enemy_spawn="Thief")
STOCK = [("Dagger", 30), ("Hard ring", 30), ("Iron sword", 40)]


def fixed_stock(monkeypatch, stock=STOCK):
    monkeypatch.setattr(encounters, "merchant_stock", lambda: list(stock))


def test_merchants_start_at_depth_11():
    assert not eligible(make_game(distance=10), MERCHANT)
    assert eligible(make_game(distance=11), MERCHANT)


def test_a_thief_merchant_is_a_bad_encounter_and_a_merchant_is_not():
    assert is_bad(THIEF) and not is_bad(MERCHANT)


def test_buying_costs_the_markup(monkeypatch):
    game = make_game(gold=100, distance=11)
    fixed_stock(monkeypatch)
    replies(monkeypatch, "1", "0")
    assert merchant(game, MERCHANT) == "left"
    assert game.player_data.loot == ["Dagger"] and game.player_data.gold == 100 - 39


def test_a_bought_item_sells_out(monkeypatch):
    game = make_game(gold=100, distance=11)
    fixed_stock(monkeypatch)
    replies(monkeypatch, "1", "1", "0")
    merchant(game, MERCHANT)
    assert game.player_data.loot == ["Dagger"]


def test_charisma_only_sways_the_merchant_if_the_row_says_so(monkeypatch):
    game = make_game(charisma=100, gold=100, distance=11)
    fixed_stock(monkeypatch)
    replies(monkeypatch, "1", "0")
    merchant(game, dict(MERCHANT, Charisma_effect="yes"))
    assert game.player_data.gold == 100 - 33          # 39, 15% off


def test_selling_pays_35_percent_and_unequips_the_last_copy(monkeypatch):
    game = make_game(gold=0, distance=11, loot=["Hard ring"], equipped="Hard ring")
    fixed_stock(monkeypatch)
    replies(monkeypatch, "s", "1", "0")
    merchant(game, MERCHANT)
    assert game.player_data.loot == [] and game.player_data.equipped is None
    from items.items_data import get_item_price
    assert game.player_data.gold == sell_price(game, "Hard ring") == int(get_item_price("Hard ring") * 0.35)


def test_potions_sell_against_their_shop_price(monkeypatch):
    assert sell_price(make_game(), "Health potion") == 5


def test_merchants_stock_shop_items_and_sometimes_a_rare_one(monkeypatch):
    from items.items_data import is_item_buyable
    monkeypatch.setattr("adventures.encounters.random.randint", lambda a, b: 1)
    stock = merchant_stock()
    assert len(stock) == 4
    assert all(is_item_buyable(name) for name, _ in stock[:3])
    assert not is_item_buyable(stock[3][0])
    monkeypatch.setattr("adventures.encounters.random.randint", lambda a, b: 100)
    assert len(merchant_stock()) == 3


def test_buying_from_a_thief_takes_your_gold_and_starts_a_surprise_fight(monkeypatch):
    game = make_game(gold=100, distance=12)
    fixed_stock(monkeypatch)
    fights = record_fights(monkeypatch, result="defeat")
    replies(monkeypatch, "1")
    assert merchant(game, THIEF) == "defeat"
    assert fights == [{"enemy": "Thief", "size": 1, "surprise": True, "scaling": 11}]
    assert game.player_data.gold == 61 and game.player_data.loot == []


def test_beating_the_thief_gets_the_gold_back_but_not_the_item(monkeypatch):
    game = make_game(gold=100, distance=12)
    fixed_stock(monkeypatch)
    record_fights(monkeypatch)
    replies(monkeypatch, "1")
    assert merchant(game, THIEF) == "victory"
    assert game.player_data.gold == 100 and game.player_data.loot == []


def test_selling_to_a_thief_and_winning_gets_the_item_back(monkeypatch):
    game = make_game(gold=0, distance=12, loot=["Dagger"])
    fixed_stock(monkeypatch)
    record_fights(monkeypatch)
    replies(monkeypatch, "s", "1")
    merchant(game, THIEF)
    assert game.player_data.loot == ["Dagger"] and game.player_data.gold == 0


def test_selling_to_a_thief_and_losing_loses_the_item(monkeypatch):
    game = make_game(gold=0, distance=12, loot=["Dagger"])
    fixed_stock(monkeypatch)
    record_fights(monkeypatch, result="defeat")
    replies(monkeypatch, "s", "1")
    merchant(game, THIEF)
    assert game.player_data.loot == [] and game.player_data.gold == 0


def test_just_looking_at_a_thief_is_safe(monkeypatch):
    game = make_game(gold=100, distance=12)
    fixed_stock(monkeypatch)
    fights = record_fights(monkeypatch)
    replies(monkeypatch, "c1", "", "0")
    assert merchant(game, THIEF) == "left"
    assert fights == [] and game.player_data.gold == 100


def test_a_sharp_mind_can_see_a_thief(monkeypatch, capsys):
    game = make_game(intelligence=30, distance=12)
    fixed_stock(monkeypatch)
    monkeypatch.setattr("adventures.encounters.random.randint", lambda a, b: 1)
    replies(monkeypatch, "0")
    merchant(game, THIEF)
    out = capsys.readouterr().out
    assert any(flavor in out for flavor in encounters.NOTICE_FLAVOR["Merchant"]), out


def test_bulk_selling_a_stack(monkeypatch):
    game = make_game(gold=0, distance=11, loot=["Nuts"] * 4 + ["Dagger"])
    fixed_stock(monkeypatch)
    replies(monkeypatch, "s", "1", "3", "0", "0")
    merchant(game, MERCHANT)
    assert game.player_data.loot == ["Nuts", "Dagger"]
    assert game.player_data.gold == sell_price(game, "Nuts") * 3


def test_a_sells_the_whole_stack_and_the_menu_stays_open_for_more(monkeypatch):
    game = make_game(gold=0, distance=11, loot=["Nuts"] * 4 + ["Dagger"])
    fixed_stock(monkeypatch)
    replies(monkeypatch, "s", "1", "a", "1", "0", "0")      # all the Nuts, then the Dagger
    merchant(game, MERCHANT)
    assert game.player_data.loot == []
    assert game.player_data.gold == sell_price(game, "Nuts") * 4 + sell_price(game, "Dagger")


def test_enter_sells_just_one_and_too_many_sells_them_all(monkeypatch):
    game = make_game(gold=0, distance=11, loot=["Nuts"] * 4)
    fixed_stock(monkeypatch)
    replies(monkeypatch, "s", "1", "", "1", "99", "0")
    merchant(game, MERCHANT)
    assert game.player_data.loot == []


def test_a_thief_takes_the_whole_bulk_sale_and_gives_it_all_back_if_you_win(monkeypatch):
    game = make_game(gold=0, distance=12, loot=["Nuts"] * 4)
    fixed_stock(monkeypatch)
    record_fights(monkeypatch)
    replies(monkeypatch, "s", "1", "a")
    merchant(game, THIEF)
    assert game.player_data.loot == ["Nuts"] * 4 and game.player_data.gold == 0
