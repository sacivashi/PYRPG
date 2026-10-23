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
    assert game.player_data.quest_flags["lost_cat"] == 1


def test_matching_is_case_insensitive():
    game = make_game()
    game._update_quest_progress("CAT")
    assert game.player_data.quest_flags["lost_cat"] == 1


def test_defeating_a_different_enemy_does_not_set_the_flag():
    game = make_game()
    game._update_quest_progress("Bandit")
    assert "lost_cat" not in game.player_data.quest_flags


def test_a_group_of_cats_also_sets_the_flag():
    # group encounters still pass the single shared enemy_name to _update_quest_progress
    game = make_game()
    game._update_quest_progress("Cat")
    assert game.player_data.quest_flags.get("lost_cat") == 1


# --- quest board ------------------------------------------------------------------------

def test_board_shows_in_progress_before_the_cat_is_defeated(monkeypatch, capsys):
    game = make_game()
    monkeypatch.setattr("builtins.input", lambda *_: "")
    game.quest_board()
    assert "In progress" in capsys.readouterr().out


def test_claiming_the_quest_awards_gold_and_marks_it_completed(monkeypatch):
    game = make_game()
    game.player_data.quest_flags["lost_cat"] = 1
    monkeypatch.setattr("builtins.input", lambda *_: "yes")

    game.quest_board()

    assert game.player_data.gold == 30
    assert "lost_cat" in game.player_data.completed_quests


def test_declining_the_claim_leaves_it_unclaimed(monkeypatch):
    game = make_game()
    game.player_data.quest_flags["lost_cat"] = 1
    monkeypatch.setattr("builtins.input", lambda *_: "no")

    game.quest_board()

    assert game.player_data.gold == 0
    assert "lost_cat" not in game.player_data.completed_quests


def test_completed_quest_cannot_be_claimed_again(monkeypatch):
    game = make_game()
    game.player_data.quest_flags["lost_cat"] = 1
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
    monkeypatch.setattr("game.pyrpg.get_encounter_enemy", lambda power, depth=None: "Cat")
    monkeypatch.setattr("game.pyrpg.roll_group_size", lambda depth=0: 1)
    monkeypatch.setattr("game.pyrpg.start_combat", lambda player_data, enemy_name, group_size: ("victory", 30, None))
    monkeypatch.setattr(game, "auto_save_player_state", lambda: None)
    monkeypatch.setattr(game, "_process_level_ups", lambda: None)
    monkeypatch.setattr(game, "_roll_for_loot", lambda: None)
    monkeypatch.setattr("builtins.input", lambda *_: "")

    game.enter_combat()

    assert game.player_data.quest_flags.get("lost_cat") == 1


def test_victory_over_something_else_does_not_touch_quest_progress(monkeypatch):
    game = make_game()
    monkeypatch.setattr("game.pyrpg.get_encounter_enemy", lambda power, depth=None: "Bandit")
    monkeypatch.setattr("game.pyrpg.roll_group_size", lambda depth=0: 1)
    monkeypatch.setattr("game.pyrpg.start_combat", lambda player_data, enemy_name, group_size: ("victory", 30, None))
    monkeypatch.setattr(game, "auto_save_player_state", lambda: None)
    monkeypatch.setattr(game, "_process_level_ups", lambda: None)
    monkeypatch.setattr(game, "_roll_for_loot", lambda: None)
    monkeypatch.setattr("builtins.input", lambda *_: "")

    game.enter_combat()

    assert "lost_cat" not in game.player_data.quest_flags


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


# --- data/quests.csv ----------------------------------------------------------------------

def test_quests_load_from_the_csv():
    from quests.quests_data import get_quests
    lost_cat = get_quests()["lost_cat"]
    assert lost_cat["type"] == "defeat" and lost_cat["target"] == "Cat"
    assert lost_cat["amount"] == 1 and lost_cat["reward"] == 30


def test_a_save_from_before_quests_csv_still_counts_as_done(monkeypatch):
    game = make_game(quest_flags={"defeated_cat": True})   # how Beta I saved a finished Lost Cat
    monkeypatch.setattr("builtins.input", lambda *_: "yes")
    game.quest_board()
    assert "lost_cat" in game.player_data.completed_quests


def use_quests(monkeypatch, tmp_path, rows):
    path = tmp_path / "quests.csv"
    path.write_text("id,title,type,target,amount,reward,description\n" + "\n".join(rows) + "\n")
    monkeypatch.setenv("QUESTS_CSV", str(path))


def test_multi_kill_quests_count_up_and_cap_at_the_amount(monkeypatch, tmp_path):
    use_quests(monkeypatch, tmp_path, ['wolves,Wolf Pack,defeat,Wolf,5,60,"Thin out the wolves."'])
    game = make_game()
    game._update_quest_progress("Wolf")
    game._update_quest_progress("Wolf", defeated=3)          # a group of 3
    assert game.player_data.quest_flags["wolves"] == 4
    game._update_quest_progress("Wolf", defeated=3)
    assert game.player_data.quest_flags["wolves"] == 5


def test_board_shows_progress_and_only_pays_once_its_done(monkeypatch, tmp_path, capsys):
    use_quests(monkeypatch, tmp_path, ['wolves,Wolf Pack,defeat,Wolf,5,60,"Thin out the wolves."'])
    game = make_game(quest_flags={"wolves": 2})
    monkeypatch.setattr("builtins.input", lambda *_: "yes")
    game.quest_board()
    assert "In progress (2/5)" in capsys.readouterr().out
    assert game.player_data.gold == 0


def test_a_group_victory_counts_every_enemy(monkeypatch, tmp_path):
    use_quests(monkeypatch, tmp_path, ['wolves,Wolf Pack,defeat,Wolf,5,60,"Thin out the wolves."'])
    game = make_game()
    monkeypatch.setattr("game.pyrpg.get_encounter_enemy", lambda power, depth=None: "Wolf")
    monkeypatch.setattr("game.pyrpg.roll_group_size", lambda depth=0: 3)
    monkeypatch.setattr("game.pyrpg.start_combat", lambda player_data, enemy_name, group_size: ("victory", 30, None))
    monkeypatch.setattr(game, "auto_save_player_state", lambda: None)
    monkeypatch.setattr(game, "_process_level_ups", lambda: None)
    monkeypatch.setattr(game, "_roll_for_loot", lambda: None)
    monkeypatch.setattr("builtins.input", lambda *_: "")
    game.enter_combat()
    assert game.player_data.quest_flags["wolves"] == 3


# --- "use" quests and perk rewards (Fast Travel System) -----------------------------------

def test_fast_travel_quest_loads_with_a_perk_reward():
    from quests.quests_data import get_quests
    quest = get_quests()["fast_travel_system"]
    assert quest["type"] == "use" and quest["reward"] == "free_fast_travel"


def test_fast_travelling_completes_the_quest_and_the_perk_makes_the_next_trip_free(monkeypatch):
    game = make_game(depth_reached=10, gold=100)
    replies = iter(["10", "", "yes", "", "10", ""])  # travel, enter, claim, enter, travel, enter
    monkeypatch.setattr("builtins.input", lambda *_: next(replies, ""))

    game.fast_travel()                                    # paid trip: 25 gold, counts for the quest
    assert game.player_data.gold == 75
    assert game.player_data.quest_flags["fast_travel_system"] == 1

    game.player_data.in_town = True
    game.quest_board()                                    # claims everything that's ready
    assert "fast_travel_system" in game.player_data.completed_quests
    assert game.player_data.perks == ["free_fast_travel"]

    game.fast_travel()                                    # free trip uses the perk up
    assert game.player_data.gold == 75
    assert game.player_data.perks == []


def test_the_free_trip_perk_survives_save_and_load(monkeypatch, tmp_path):
    monkeypatch.setenv("PLAYERS_JSON", str(tmp_path / "players.json"))
    pd = PlayerData(name="PerkTest", role="warrior", level=1, hp=30, stats=dict(STATS), max_hp=30,
                    perks=["free_fast_travel"])
    put_new_player(Player(pd))
    assert get_player("PerkTest").perks == ["free_fast_travel"]
