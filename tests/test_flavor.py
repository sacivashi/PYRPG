"""v1.0.7 flavor text: chances, placeholders, and where it's said"""
import pytest

from util import flavor
from util.flavor import FLAVOR, line, say, win_moment


@pytest.fixture
def always(monkeypatch):
    monkeypatch.setattr(flavor._rng, "uniform", lambda a, b: 0)


@pytest.fixture
def never(monkeypatch):
    monkeypatch.setattr(flavor._rng, "uniform", lambda a, b: 100)


def test_every_line_fills_in(always):
    for moment, (chance, lines) in FLAVOR.items():
        assert 0 < chance <= 100 and lines
        for text in lines:
            filled = text.format_map(flavor._Blank(enemy="Wolf", name="Bob", item="Rum", gold=5, tier="S"))
            assert "{" not in filled.replace("{insert", "") , text


def test_chance(always, capsys):
    assert say("missed", enemy="Wolf")
    assert "»" in capsys.readouterr().out


def test_no_line_when_the_chance_misses(never, capsys):
    assert say("missed", enemy="Wolf") is None
    assert capsys.readouterr().out == ""


def test_a_missing_placeholder_doesnt_crash(always):
    assert line("slain")          # no enemy or name given


def test_win_bands():
    assert win_moment(40, 40) == "win_high" and win_moment(30, 40) == "win_high"
    assert win_moment(29, 40) == "win_mid" and win_moment(20, 40) == "win_mid"
    assert win_moment(19, 40) == "win_low"


def test_flavor_doesnt_touch_the_games_dice(monkeypatch, always):
    import random
    monkeypatch.setattr(random, "uniform", lambda a, b: (_ for _ in ()).throw(AssertionError("game dice")))
    monkeypatch.setattr(random, "choice", lambda seq: (_ for _ in ()).throw(AssertionError("game dice")))
    say("level_up")


def test_death_says_cannot_flee_without_a_line(monkeypatch, never, capsys):
    from combat.combat import Combat
    from players.player_data import PlayerData
    stats = {'Strength': 5, 'Agility': 5, 'Intelligence': 0, 'Charisma': 0, 'Defense': 5, 'Magic': 5, 'Luck': 5}
    combat = Combat(PlayerData(name="T", role="warrior", level=1, hp=40, stats=stats, max_hp=40), "Death")
    combat.current_turn = "player"
    answers = iter(["6", "4"])
    monkeypatch.setattr("builtins.input", lambda *_: next(answers))
    combat.player_turn()
    assert "You cannot flee." in capsys.readouterr().out


def test_rest_ambush_names_the_enemy(monkeypatch, always, capsys):
    from game.pyrpg import PYRPG
    from players.player_data import PlayerData
    game = PYRPG.__new__(PYRPG)
    game.player_data = PlayerData(name="T", role="warrior", level=1, hp=40, stats={}, max_hp=40)
    monkeypatch.setattr("game.pyrpg.get_encounter_enemy", lambda *_: "Wolf")
    monkeypatch.setattr("game.pyrpg.roll_group_size", lambda *_: 1)
    monkeypatch.setattr(PYRPG, "fight", lambda self, *a, **k: None)
    monkeypatch.setattr(flavor._rng, "choice", lambda seq: next((s for s in seq if "{enemy}" in s), seq[0]))
    game.enter_combat(flavor="rest_fail")
    assert "Wolf" in capsys.readouterr().out.split("\n")[0]


def test_a_line_takes_the_plain_messages_place(always, capsys):
    say("flee_fail", instead="You fail to escape!", name="Bob", enemy="Wolf")
    out = capsys.readouterr().out
    assert "»" in out and "You fail to escape!" not in out


def test_the_plain_message_when_no_line_comes_up(never, capsys):
    say("flee_fail", instead="You fail to escape!", name="Bob", enemy="Wolf")
    assert capsys.readouterr().out == "You fail to escape!\n"
