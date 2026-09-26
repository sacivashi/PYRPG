from combat.combat_player import Player
from game.pyrpg import PYRPG
from players.player_data import PlayerData
from players.save import put_new_player
from util.file_io import get_player

STATS = {'Strength': 5, 'Agility': 5, 'Intelligence': 0, 'Defence': 5, 'Magic': 5, 'Luck': 5}


def make_game(**overrides):
    game = PYRPG.__new__(PYRPG)
    game.player_data = PlayerData(name="T", role="warrior", level=1, hp=30, stats=dict(STATS), max_hp=30, **overrides)
    return game


# --- progress tracking ----------------------------------------------------------------

def test_defeating_a_cat_sets_the_quest_flag():
    game = make_game()
    game._update_quest_progress("Cat")
    assert game.player_data.quest_flags["defeated_cat"] is True


def test_matching_is_case_insensitive():
    game = make_game()
    game._update_quest_progress("CAT")
    assert game.player_data.quest_flags["defeated_cat"] is True


def test_defeating_a_different_enemy_does_not_set_the_flag():
    game = make_game()
    game._update_quest_progress("Bandit")
    assert "defeated_cat" not in game.player_data.quest_flags


def test_a_group_of_cats_also_sets_the_flag():
    # group encounters still pass the single shared enemy_name to _update_quest_progress
    game = make_game()
    game._update_quest_progress("Cat")
    assert game.player_data.quest_flags.get("defeated_cat") is True


# --- quest board ------------------------------------------------------------------------

def test_board_shows_in_progress_before_the_cat_is_defeated(monkeypatch, capsys):
    game = make_game()
    monkeypatch.setattr("builtins.input", lambda *_: "")
    game.quest_board()
    assert "In progress" in capsys.readouterr().out


def test_claiming_the_quest_awards_gold_and_marks_it_completed(monkeypatch):
    game = make_game()
    game.player_data.quest_flags["defeated_cat"] = True
    monkeypatch.setattr("builtins.input", lambda *_: "yes")

    game.quest_board()

    assert game.player_data.gold == 30
    assert "lost_cat" in game.player_data.completed_quests


def test_declining_the_claim_leaves_it_unclaimed(monkeypatch):
    game = make_game()
    game.player_data.quest_flags["defeated_cat"] = True
    monkeypatch.setattr("builtins.input", lambda *_: "no")

    game.quest_board()

    assert game.player_data.gold == 0
    assert "lost_cat" not in game.player_data.completed_quests


def test_completed_quest_cannot_be_claimed_again(monkeypatch):
    game = make_game()
    game.player_data.quest_flags["defeated_cat"] = True
    game.player_data.completed_quests.append("lost_cat")
    game.player_data.gold = 0
    monkeypatch.setattr("builtins.input", lambda *_: "yes")  # even if asked, shouldn't be able to say yes again

    game.quest_board()

    assert game.player_data.gold == 0  # no second reward
    assert game.player_data.completed_quests.count("lost_cat") == 1


def test_board_shows_completed_status(monkeypatch, capsys):
    game = make_game()
    game.player_data.completed_quests.append("lost_cat")
    monkeypatch.setattr("builtins.input", lambda *_: "")
    game.quest_board()
    assert "Completed" in capsys.readouterr().out


# --- full enter_combat integration -------------------------------------------------------

def test_victory_over_a_cat_updates_quest_progress(monkeypatch):
    game = make_game()
    monkeypatch.setattr("game.pyrpg.get_encounter_enemy", lambda power: "Cat")
    monkeypatch.setattr("game.pyrpg.roll_group_size", lambda: 1)
    monkeypatch.setattr("game.pyrpg.start_combat", lambda player_data, enemy_name, group_size: ("victory", 30))
    monkeypatch.setattr(game, "auto_save_player_state", lambda: None)
    monkeypatch.setattr(game, "_process_level_ups", lambda: None)
    monkeypatch.setattr(game, "_roll_for_loot", lambda: None)
    monkeypatch.setattr("builtins.input", lambda *_: "")

    game.enter_combat()

    assert game.player_data.quest_flags.get("defeated_cat") is True


def test_victory_over_something_else_does_not_touch_quest_progress(monkeypatch):
    game = make_game()
    monkeypatch.setattr("game.pyrpg.get_encounter_enemy", lambda power: "Bandit")
    monkeypatch.setattr("game.pyrpg.roll_group_size", lambda: 1)
    monkeypatch.setattr("game.pyrpg.start_combat", lambda player_data, enemy_name, group_size: ("victory", 30))
    monkeypatch.setattr(game, "auto_save_player_state", lambda: None)
    monkeypatch.setattr(game, "_process_level_ups", lambda: None)
    monkeypatch.setattr(game, "_roll_for_loot", lambda: None)
    monkeypatch.setattr("builtins.input", lambda *_: "")

    game.enter_combat()

    assert "defeated_cat" not in game.player_data.quest_flags


# --- Player carry-through and save/load (the exact bug class gold/loot hit earlier) ------

def test_player_carries_quest_state_through_its_own_lifecycle():
    pd = PlayerData(name="T", role="warrior", level=1, hp=30, stats=dict(STATS), max_hp=30,
                     quest_flags={"defeated_cat": True}, completed_quests=["lost_cat"])
    player = Player(pd)
    round_tripped = player.player_data()
    assert round_tripped.quest_flags == {"defeated_cat": True}
    assert round_tripped.completed_quests == ["lost_cat"]


def test_quest_state_survives_save_and_load(monkeypatch, tmp_path):
    monkeypatch.setenv("PLAYERS_JSON", str(tmp_path / "players.json"))
    pd = PlayerData(name="QuestSaveTest", role="warrior", level=1, hp=30, stats=dict(STATS), max_hp=30,
                     quest_flags={"defeated_cat": True}, completed_quests=["lost_cat"], gold=30)
    put_new_player(Player(pd))

    loaded = get_player("QuestSaveTest")

    assert loaded.quest_flags == {"defeated_cat": True}
    assert loaded.completed_quests == ["lost_cat"]
    assert loaded.gold == 30


def test_old_saves_without_quest_fields_default_cleanly(monkeypatch, tmp_path):
    import json
    save_path = tmp_path / "players.json"
    save_path.write_text(json.dumps({"players": [{
        "name": "OldSave", "role": "warrior", "level": 1, "hp": 30, "max_hp": 30, "stats": STATS,
    }]}))
    monkeypatch.setenv("PLAYERS_JSON", str(save_path))

    loaded = get_player("OldSave")

    assert loaded.quest_flags == {}
    assert loaded.completed_quests == []
