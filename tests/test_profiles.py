"""v1.1.1 players: who's playing owns adventurers and unlocks, the start menu, and old saves moved aside"""
import json

import pytest

from players import profiles
from players.input_name import InputName
from unlocks.unlocks import grant, is_unlocked
from util import display
from util.file_io import get_adventurers, get_player


def replies(monkeypatch, *answers):
    """Answer input() in order; prompts are printed so capsys sees them too"""
    it = iter(answers)

    def answer(prompt=""):
        print(prompt)
        return next(it)
    monkeypatch.setattr("builtins.input", answer)


def saved(tmp_path):
    return json.loads((tmp_path / "players.json").read_text())["Players"]


# --- the new-player flow ----------------------------------------------------------------------------

def test_a_new_player_makes_their_first_adventurer_and_both_are_saved(monkeypatch, tmp_path):
    replies(monkeypatch, "1", "Raz", "Bee", "warrior", "y")
    pd, saving = InputName.input_name()
    assert (pd.name, pd.role, saving) == ("Bee", "warrior", True)
    assert profiles.ACTIVE == "Raz"
    assert [a["name"] for a in saved(tmp_path)["Raz"]["Adventurers"]] == ["Bee"]


def test_a_taken_player_name_offers_to_load_instead(monkeypatch, tmp_path, capsys):
    profiles.create_player("Flood")
    replies(monkeypatch, "1", "flood", "n", "Other", "Bee", "warrior", "y")
    pd, _ = InputName.input_name()
    assert "this user name is in existence" in capsys.readouterr().out
    assert set(saved(tmp_path)) == {"Flood", "Other"} and profiles.ACTIVE == "Other"


def test_empty_answers_go_back_and_exit_quits(monkeypatch):
    replies(monkeypatch, "1", "", "2", "", "3")
    with pytest.raises(SystemExit):
        InputName.input_name()


# --- my adventurers ----------------------------------------------------------------------------------

def make_adventurer(monkeypatch, player, name):
    profiles.create_player(player)
    profiles.set_active(player)
    replies(monkeypatch, name, "warrior", "y")
    from players.input_name import create_adventurer
    return create_adventurer(player)


def test_loading_lists_your_adventurers_whatever_case_you_type(monkeypatch, capsys):
    make_adventurer(monkeypatch, "unaffiliated", "Bee")
    replies(monkeypatch, "2", "UNAFFILIATED", "1", "l")
    pd, saving = InputName.input_name()
    out = capsys.readouterr().out
    assert "Welcome back unaffiliated." in out and "in town" in out
    assert pd.name == "Bee" and saving


def test_an_unknown_name_offers_a_new_player(monkeypatch, tmp_path, capsys):
    replies(monkeypatch, "2", "nobody", "y", "Bee", "warrior", "y")
    pd, _ = InputName.input_name()
    out = capsys.readouterr().out
    assert 'No player data for "nobody" found' in out and "Much obliged." in out
    assert "nobody" in saved(tmp_path)


def test_your_own_adventurer_name_is_taken_but_others_can_use_it(monkeypatch, capsys):
    make_adventurer(monkeypatch, "Raz", "Bee")
    replies(monkeypatch, "2", "raz", "2", "bee", "Gruk", "warrior", "y")
    pd, _ = InputName.input_name()
    assert "This character exists, please use a different name or load it" in capsys.readouterr().out
    assert pd.name == "Gruk"
    make_adventurer(monkeypatch, "Mira", "Bee")                   # another player's Bee is fine
    assert [a.name for a in get_adventurers("Raz")] == ["Bee", "Gruk"]
    assert [a.name for a in get_adventurers("Mira")] == ["Bee"]


def test_deleting_needs_the_name_typed_out(monkeypatch):
    make_adventurer(monkeypatch, "Raz", "Bee")
    replies(monkeypatch, "2", "raz", "1", "d", "nope", "1", "d", "BEE", "0", "", "3")
    with pytest.raises(SystemExit):
        InputName.input_name()
    assert get_adventurers("Raz") == []


# --- unlocks belong to the player -------------------------------------------------------------------

def test_unlocks_belong_to_the_player(monkeypatch):
    profiles.set_active("Raz")
    grant("class:knight")
    assert is_unlocked("class:knight")
    profiles.set_active("Mira")
    assert not is_unlocked("class:knight")


def test_nobody_playing_keeps_unlocks_in_memory(monkeypatch, tmp_path):
    monkeypatch.setattr(profiles, "_memory_unlocks", {})
    profiles.set_active(None)
    grant("class:knight")
    assert is_unlocked("class:knight") and not (tmp_path / "players.json").exists()


# --- saves from before players ------------------------------------------------------------------------

def test_old_saves_are_moved_aside_not_read(tmp_path):
    (tmp_path / "players.json").write_text(json.dumps({"players": [{"name": "Old", "role": "warrior"}]}))
    (tmp_path / "unlocks.json").write_text('{"progress": {}, "unlocked": ["class:knight"]}')
    moved = profiles.archive_old_saves()
    assert sorted(p.split("\\")[-1].split("/")[-1] for p in moved) == ["players_old.json", "unlocks_old.json"]
    assert not (tmp_path / "players.json").exists() and get_player("Old") is None
    assert "Old" in (tmp_path / "players_old.json").read_text()


def test_new_saves_and_an_existing_backup_are_left_alone(tmp_path):
    profiles.create_player("Raz")
    (tmp_path / "players_old.json").write_text("keep me")
    assert profiles.archive_old_saves() == []
    assert "Raz" in saved(tmp_path)
    (tmp_path / "players.json").write_text(json.dumps({"players": [{"name": "Old"}]}))
    profiles.archive_old_saves()
    assert (tmp_path / "players_old.json").read_text() == "keep me"
    assert "Old" in (tmp_path / "players_old (2).json").read_text()


# --- display without color ----------------------------------------------------------------------------

def test_without_color_everything_stays_plain_text():
    assert not display.ENABLED
    assert "\x1b" not in display.table(["#", "Name"], [["[1]", "Bee"]]) + display.banner("1.1.1")
    assert display.highlight("You deal 11 damage!") == "You deal 11 damage!"
    assert display.banner("1.1.1").endswith("v1.1.1")
