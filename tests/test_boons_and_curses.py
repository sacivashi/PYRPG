"""v1.0.6 prayer sculptures (boons & curses), the Prayer card, and the event bus they tick on"""
import pytest

from adventures import encounters
from adventures.encounters import prayer_card, sculpture, sculpture_fail_chance
from combat.combat_player import Player
from game.pyrpg import PYRPG
from players.player_data import PlayerData
from players.save import put_new_player
from util.effects import apply_effects, bonus, make_effect, parse_op, tick
from util.events import EventBus
from util.file_io import get_data, get_player, read_csv

STATS = {'Strength': 10, 'Agility': 5, 'Intelligence': 5, 'Charisma': 4, 'Defense': 5, 'Magic': 5, 'Luck': 8}
ROWS = {row["Description"]: row for row in read_csv(get_data("encounters_csv"))
        if row["Type"] in ("Boon", "Curse")}


def make_game(**overrides):
    game = PYRPG.__new__(PYRPG)
    defaults = dict(name="T", role="warrior", level=1, hp=10, stats=dict(STATS), gold=100,
                    in_town=False, distance=6)
    defaults.update(overrides)
    game.player_data = PlayerData(**defaults)
    game.player_data.max_hp = game._max_hp()
    return game


def replies(monkeypatch, *answers):
    it = iter(answers)
    monkeypatch.setattr("builtins.input", lambda *_: next(it, ""))


def bless(game, name):
    from adventures.encounters import receive
    return receive(game, ROWS[name])


# --- reading the rows ------------------------------------------------------------------------------

def test_every_boon_and_curse_row_reads():
    assert len(ROWS) == 8
    for row in ROWS.values():
        make_effect(row)


def test_parse_op():
    assert parse_op("+=15") == ("+", 15)
    assert parse_op("*=0") == ("*", 0)
    assert parse_op("-=999") == ("-", 999)


def test_durations():
    assert make_effect(ROWS["Of resting"])["ticks_on"] == ["rest"]
    assert make_effect(ROWS["Of survival"])["ticks_on"] == ["rested"]
    assert make_effect(ROWS["Of fear"])["left"] == 5 and make_effect(ROWS["Of fear"])["ticks_on"] == ["explore"]
    assert make_effect(ROWS["Of crippling"])["ticks_on"] == ["rested", "town_rest"]


def test_only_sculptures_from_depth_5():
    from adventures.encounters import eligible
    assert not eligible(make_game(distance=4), ROWS["Of fear"])
    assert eligible(make_game(distance=5), ROWS["Of fear"])


# --- praying ------------------------------------------------------------------------------------

def test_fail_chance_is_swayed_by_charisma():
    assert sculpture_fail_chance(0) == 10
    assert sculpture_fail_chance(20) == 5
    assert sculpture_fail_chance(80) == 0
    assert sculpture_fail_chance(-80) == 30


def test_walking_past_a_sculpture(monkeypatch):
    game = make_game()
    replies(monkeypatch, "n")
    assert sculpture(game, ROWS["Of fear"]) is None and game.player_data.effects == []


def test_the_gods_can_stay_silent(monkeypatch):
    game = make_game()
    replies(monkeypatch, "y", "")
    monkeypatch.setattr("adventures.encounters.random.randint", lambda a, b: 9)   # Charisma 4: 9% fail
    assert sculpture(game, ROWS["Of resting"]) is None and game.player_data.effects == []


def test_praying_gives_the_rows_effect(monkeypatch):
    game = make_game()
    replies(monkeypatch, "y", "")
    monkeypatch.setattr("adventures.encounters.random.randint", lambda a, b: 10)
    assert sculpture(game, ROWS["Of resting"])["name"] == "Of resting"
    assert [e["name"] for e in game.player_data.effects] == ["Of resting"]


def test_praying_twice_refreshes_instead_of_stacking():
    game = make_game()
    bless(game, "Of resting")
    tick(game.player_data.effects, "rest")
    bless(game, "Of resting")
    assert len(game.player_data.effects) == 1 and game.player_data.effects[0]["left"] == 3


# --- boons ----------------------------------------------------------------------------------------

def test_of_resting_adds_15_to_rest_odds_for_3_attempts(monkeypatch):
    game = make_game()
    base = game.calculate_rest_chance()
    bless(game, "Of resting")
    assert game.calculate_rest_chance() == base + 15
    monkeypatch.setattr(PYRPG, "enter_combat", lambda self: None)
    monkeypatch.setattr("game.pyrpg.random.randint", lambda a, b: 100)   # every rest fails
    replies(monkeypatch)
    for _ in range(3):
        game.rest()
    assert game.player_data.effects == []


def test_of_survival_rests_heal_45_percent_and_only_successes_count(monkeypatch):
    game = make_game(hp=1)
    bless(game, "Of survival")
    replies(monkeypatch)
    monkeypatch.setattr(PYRPG, "enter_combat", lambda self: None)
    monkeypatch.setattr("game.pyrpg.random.randint", lambda a, b: 100)   # a failed rest...
    game.rest()
    assert game.player_data.effects[0]["left"] == 3                     # ...doesn't use it up
    monkeypatch.setattr("game.pyrpg.random.randint", lambda a, b: 1)
    game.rest()
    assert game.player_data.hp == 1 + round(game.player_data.max_hp * 0.45)
    assert game.player_data.effects[0]["left"] == 2


def stub_win(monkeypatch, gold=10, exp=10.0):
    monkeypatch.setattr("game.pyrpg.start_combat", lambda pd, enemy, size: ("victory", pd.hp, None))
    monkeypatch.setattr(PYRPG, "calculate_gold_reward", lambda self: gold)
    monkeypatch.setattr(PYRPG, "calculate_exp_reward", lambda self, enemy: exp)
    monkeypatch.setattr(PYRPG, "_roll_for_loot", lambda self: None)
    monkeypatch.setattr(PYRPG, "auto_save_player_state", lambda self: None)
    replies(monkeypatch)


def test_of_prosperity_and_of_intellect_pay_out_on_the_next_win_only(monkeypatch):
    game = make_game(gold=0)
    bless(game, "Of prosperity")
    bless(game, "Of intellect")
    stub_win(monkeypatch, gold=100, exp=10.0)
    game.fight("Wolf")
    assert game.player_data.gold == 112 and game.player_data.exp == pytest.approx(13)
    assert game.player_data.effects == []
    game.fight("Wolf")
    assert game.player_data.gold == 212


def test_of_growth_raises_max_hp_heals_and_lasts_until_a_win(monkeypatch):
    game = make_game(hp=5)
    normal_max = game.player_data.max_hp
    bless(game, "Of growth")
    assert game.player_data.max_hp == normal_max + 15 and game.player_data.hp == normal_max + 15
    assert Player(game.player_data).max_hp == normal_max + 15             # combat sees it too
    stub_win(monkeypatch)
    game.fight("Wolf")
    assert game.player_data.max_hp == normal_max and game.player_data.hp == normal_max


# --- curses -------------------------------------------------------------------------------------

def test_of_fear_drops_charisma_by_999_for_5_explores(monkeypatch):
    game = make_game()
    bless(game, "Of fear")
    assert game._charisma() == 4 - 999
    assert game.player_data.stats["Charisma"] == 4                       # the saved stat is untouched
    monkeypatch.setattr(PYRPG, "passive_encounter", lambda self: True)
    for _ in range(5):
        game.explore()
    assert game._charisma() == 4


def test_of_crippling_zeroes_strength_in_combat_until_a_rest(monkeypatch):
    game = make_game(hp=40)
    bless(game, "Of crippling")
    assert game._effective_stats()["Strength"] == 0
    assert Player(game.player_data).stats["Strength"] == 0
    assert game.player_data.max_hp == Player.calculate_hp(dict(STATS, Strength=0))
    monkeypatch.setattr("game.pyrpg.random.randint", lambda a, b: 1)
    replies(monkeypatch)
    game.rest()
    assert game._effective_stats()["Strength"] == 10 and game.player_data.effects == []


def test_a_town_rest_lifts_curses_and_heals_to_the_uncursed_max(monkeypatch):
    game = make_game(in_town=True)
    bless(game, "Of misery")
    replies(monkeypatch)
    game.full_rest()
    assert game.player_data.effects == []
    assert game.player_data.hp == game.player_data.max_hp == game._max_hp()


def test_curses_dont_make_encounters_easier():
    game = make_game()
    power = game._player_power()
    bless(game, "Of crippling")
    assert game._player_power() == power


def test_effects_apply_on_top_of_gear():
    assert apply_effects({"Strength": 5}, [make_effect(ROWS["Of crippling"])]) == {"Strength": 0}
    assert bonus([], "gold", 10) == 10


# --- never saved --------------------------------------------------------------------------------

def test_boons_and_curses_are_never_saved(monkeypatch, tmp_path):
    monkeypatch.setenv("PLAYERS_JSON", str(tmp_path / "players.json"))
    (tmp_path / "players.json").write_text('{"players": []}')
    game = make_game(name="Cursed")
    bless(game, "Of crippling")
    put_new_player(Player(game.player_data))
    assert "effects" not in (tmp_path / "players.json").read_text()
    loaded = get_player("Cursed")
    assert loaded.effects == [] and loaded.stats["Strength"] == 10


# --- the Prayer card -----------------------------------------------------------------------------

def test_the_prayer_card_gives_a_boon_or_curse_and_is_used_up(monkeypatch):
    game = make_game(loot=["Prayer card"])
    assert game.use_item_outside_combat("Prayer card")
    assert game.player_data.loot == [] and len(game.player_data.effects) == 1
    assert game.player_data.effects[0]["name"] in ROWS


def test_the_prayer_card_is_in_the_shop():
    from items.items_data import is_item_buyable, is_item_consumable, is_item_droppable
    assert is_item_buyable("Prayer card") and is_item_consumable("Prayer card")
    assert not is_item_droppable("Prayer card")


# --- the event bus -------------------------------------------------------------------------------

def test_event_bus():
    bus, heard = EventBus(), []
    bus.on("victory", lambda enemy, size: heard.append((enemy, size)))
    bus.emit("victory", enemy="Wolf", size=2)
    bus.emit("explore", distance=3)            # nobody listening: fine
    assert heard == [("Wolf", 2)]


def test_quests_still_count_through_the_events(monkeypatch):
    game = make_game(accepted_quests=["spooky_area"], distance=14)
    monkeypatch.setattr(PYRPG, "passive_encounter", lambda self: True)
    game.explore()
    assert game.player_data.quest_flags["spooky_area"] == 1
