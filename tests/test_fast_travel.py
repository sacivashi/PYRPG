from game.pyrpg import PYRPG
from players.player_data import PlayerData
from combat.combat_player import Player

STATS = {'Strength': 5, 'Agility': 5, 'Intelligence': 5, 'Defence': 5, 'Magic': 5, 'Luck': 5}


def make_game(**overrides):
    game = PYRPG.__new__(PYRPG)
    defaults = dict(name="T", role="warrior", level=1, hp=30, stats=dict(STATS), max_hp=30, gold=100)
    defaults.update(overrides)
    game.player_data = PlayerData(**defaults)
    return game


def answer(monkeypatch, *responses):
    replies = iter(responses)
    monkeypatch.setattr("builtins.input", lambda *_: next(replies, ""))


def test_exploring_deeper_raises_depth_reached(monkeypatch):
    game = make_game(in_town=False, distance=4, depth_reached=4)
    monkeypatch.setattr(game, "enter_combat", lambda: None)
    game.explore()
    assert game.player_data.depth_reached == 5


def test_depth_reached_never_goes_down(monkeypatch):
    game = make_game(in_town=False, distance=2, depth_reached=10)
    monkeypatch.setattr(game, "enter_combat", lambda: None)
    game.explore()
    assert game.player_data.depth_reached == 10


def test_fast_travel_cost_formula():
    assert PYRPG.fast_travel_cost(1) == 2
    assert PYRPG.fast_travel_cost(10) == 25
    assert PYRPG.fast_travel_cost(21) == 52


def test_fast_travel_moves_you_and_charges_gold(monkeypatch):
    game = make_game(depth_reached=10, gold=100)
    answer(monkeypatch, "8")
    game.fast_travel()
    assert game.player_data.in_town is False
    assert game.player_data.distance == 8
    assert game.player_data.gold == 80


def test_cannot_fast_travel_past_depth_reached(monkeypatch):
    game = make_game(depth_reached=5, gold=100)
    answer(monkeypatch, "6")
    game.fast_travel()
    assert game.player_data.in_town is True
    assert game.player_data.gold == 100


def test_cannot_fast_travel_without_enough_gold(monkeypatch):
    game = make_game(depth_reached=10, gold=10)
    answer(monkeypatch, "10")
    game.fast_travel()
    assert game.player_data.in_town is True
    assert game.player_data.gold == 10


def test_nothing_to_fast_travel_to_on_a_new_character(monkeypatch):
    game = make_game(depth_reached=0)
    answer(monkeypatch)
    game.fast_travel()
    assert game.player_data.in_town is True


def test_depth_reached_survives_the_combat_player_round_trip():
    pd = make_game(depth_reached=17).player_data
    assert Player(pd).player_data().depth_reached == 17
