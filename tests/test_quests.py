from combat.combat_player import Player
from game.pyrpg import PYRPG
from players.player_data import PlayerData
from players.save import put_new_player
from util.file_io import get_player

STATS = {'Strength': 5, 'Agility': 5, 'Intelligence': 0, 'Charisma': 0, 'Defense': 5, 'Magic': 5, 'Luck': 5}
HEADER = "id,title,type,target,amount,reward,charisma,choice,description,spawn"


def make_game(**overrides):
    game = PYRPG.__new__(PYRPG)
    game.player_data = PlayerData(name="T", role="warrior", level=1, hp=30, stats=dict(STATS), max_hp=30, **overrides)
    return game


def use_quests(monkeypatch, tmp_path, rows):
    path = tmp_path / "quests.csv"
    path.write_text(HEADER + "\n" + "\n".join(rows) + "\n")
    monkeypatch.setenv("QUESTS_CSV", str(path))


def replies(monkeypatch, *answers):
    """Script the player's inputs; once they run out, Enter (which also leaves the board)"""
    answers = iter(answers)
    monkeypatch.setattr("builtins.input", lambda *_: next(answers, ""))


def board_number(game, quest_id):
    """The quest's [number] on the board right now"""
    return str([q for q, _ in game._visible_quests()].index(quest_id) + 1)


WOLVES = 'wolves,Wolf Pack,defeat,Wolf,5,60,2,,"Thin out the wolves.",'
CAT = 'cat,Lost Cat,defeat,Cat,1,30,1,,"Find the cat.",'
WALLET = 'wallet,Lost Wallet,defeat,Bandit,1,20/60,+1/-3,Give/Take wallet,"A wallet.",'
CHARITY = 'charity,Charity,spend,55/0,1,Dice machine/0,+2/-2,"Accept"/"Decline","Give gold.",'
RAID = 'raid,Townfolk Raid,defeat,Townfolk,3,80,-5,,"Shady.",Townfolk *3'


# --- progress only counts once a quest is accepted ----------------------------------------

def test_an_accepted_quest_counts_progress():
    game = make_game(accepted_quests=["lost_cat"])
    game.quest_event("defeat", "Cat")
    assert game.player_data.quest_flags["lost_cat"] == 1


def test_a_quest_you_havent_accepted_counts_nothing():
    game = make_game()
    game.quest_event("defeat", "Cat")
    assert "lost_cat" not in game.player_data.quest_flags


def test_matching_is_case_insensitive():
    game = make_game(accepted_quests=["lost_cat"])
    game.quest_event("defeat", "CAT")
    assert game.player_data.quest_flags["lost_cat"] == 1


def test_defeating_a_different_enemy_does_not_count():
    game = make_game(accepted_quests=["lost_cat"])
    game.quest_event("defeat", "Bandit")
    assert "lost_cat" not in game.player_data.quest_flags


def test_multi_kill_quests_count_up_and_cap_at_the_amount(monkeypatch, tmp_path):
    use_quests(monkeypatch, tmp_path, [WOLVES])
    game = make_game(accepted_quests=["wolves"])
    game.quest_event("defeat", "Wolf")
    game.quest_event("defeat", "Wolf", 3)          # a group of 3
    assert game.player_data.quest_flags["wolves"] == 4
    game.quest_event("defeat", "Wolf", 3)
    assert game.player_data.quest_flags["wolves"] == 5


# --- the board: accept, not now, progress, claim ------------------------------------------

def test_new_quests_show_as_new_and_accepting_takes_them(monkeypatch, tmp_path, capsys):
    use_quests(monkeypatch, tmp_path, [CAT])
    game = make_game()
    replies(monkeypatch, "1", "1")                 # open Lost Cat, accept
    game.quest_board()
    assert "Lost Cat - New" in capsys.readouterr().out
    assert game.player_data.accepted_quests == ["cat"]


def test_not_now_leaves_a_quest_on_the_board(monkeypatch, tmp_path):
    use_quests(monkeypatch, tmp_path, [CAT])
    game = make_game()
    replies(monkeypatch, "1", "0")
    game.quest_board()
    assert game.player_data.accepted_quests == []


def test_board_shows_progress_and_only_pays_once_its_done(monkeypatch, tmp_path, capsys):
    use_quests(monkeypatch, tmp_path, [WOLVES])
    game = make_game(accepted_quests=["wolves"], quest_flags={"wolves": 2})
    replies(monkeypatch, "1", "1")
    game.quest_board()
    assert "In progress (2/5)" in capsys.readouterr().out
    assert game.player_data.gold == 0


def test_claiming_awards_the_reward_and_the_charisma(monkeypatch, tmp_path):
    use_quests(monkeypatch, tmp_path, [WOLVES])
    game = make_game(accepted_quests=["wolves"], quest_flags={"wolves": 5})
    replies(monkeypatch, "1", "1")                 # open, claim
    game.quest_board()
    assert game.player_data.gold == 60
    assert game.player_data.stats["Charisma"] == 2
    assert "wolves" in game.player_data.completed_quests


def test_not_now_leaves_a_finished_quest_unclaimed(monkeypatch, tmp_path):
    use_quests(monkeypatch, tmp_path, [WOLVES])
    game = make_game(accepted_quests=["wolves"], quest_flags={"wolves": 5})
    replies(monkeypatch, "1", "0")
    game.quest_board()
    assert game.player_data.gold == 0
    assert "wolves" not in game.player_data.completed_quests


def test_completed_quest_cannot_be_claimed_again(monkeypatch, tmp_path, capsys):
    use_quests(monkeypatch, tmp_path, [WOLVES])
    game = make_game(accepted_quests=["wolves"], quest_flags={"wolves": 5}, completed_quests=["wolves"])
    replies(monkeypatch, "1", "1", "1")
    game.quest_board()
    assert game.player_data.gold == 0
    assert game.player_data.completed_quests.count("wolves") == 1
    assert "Wolf Pack - Completed" in capsys.readouterr().out


# --- choices ------------------------------------------------------------------------------

def test_choice_quests_parse_one_option_per_choice(monkeypatch, tmp_path):
    from quests.quests_data import get_quests
    use_quests(monkeypatch, tmp_path, [CHARITY, WALLET])
    quests = get_quests()
    assert quests["charity"]["options"] == [
        {"label": "Accept", "cost": 55, "reward": "dice machine", "charisma": 2},
        {"label": "Decline", "cost": 0, "reward": 0, "charisma": -2},
    ]
    assert [o["label"] for o in quests["wallet"]["options"]] == ["Give", "Take wallet"]


def test_a_choice_quest_pays_out_the_option_you_pick(monkeypatch, tmp_path):
    use_quests(monkeypatch, tmp_path, [WALLET])
    game = make_game(accepted_quests=["wallet"], quest_flags={"wallet": 1})
    replies(monkeypatch, "1", "2")                 # open, Take wallet
    game.quest_board()
    assert game.player_data.gold == 60
    assert game.player_data.stats["Charisma"] == -3
    assert game.player_data.quest_choices == {"wallet": "Take wallet"}
    assert "wallet" in game.player_data.completed_quests


def test_spend_quests_take_the_gold_and_give_the_item(monkeypatch, tmp_path):
    use_quests(monkeypatch, tmp_path, [CHARITY])
    game = make_game(gold=60)
    replies(monkeypatch, "1", "1")                 # open Charity, Accept
    game.quest_board()
    assert game.player_data.gold == 5
    assert "Dice machine" in game.player_data.loot
    assert game.player_data.stats["Charisma"] == 2


def test_declining_still_completes_the_quest(monkeypatch, tmp_path):
    use_quests(monkeypatch, tmp_path, [CHARITY])
    game = make_game(gold=60)
    replies(monkeypatch, "1", "2")                 # open Charity, Decline
    game.quest_board()
    assert game.player_data.gold == 60
    assert game.player_data.stats["Charisma"] == -2
    assert "charity" in game.player_data.completed_quests


def test_you_cant_pick_a_choice_you_cant_afford(monkeypatch, tmp_path):
    use_quests(monkeypatch, tmp_path, [CHARITY])
    game = make_game(gold=20)
    replies(monkeypatch, "1", "1")
    game.quest_board()
    assert game.player_data.gold == 20
    assert "charity" not in game.player_data.completed_quests


def test_a_zero_reward_reads_as_nothing():
    from quests.quests_data import describe_reward
    assert describe_reward(0) is None
    assert describe_reward(30) == "30 gold"


# --- quest enemies and quest chains --------------------------------------------------------

def stub_fights(monkeypatch, game, result="victory"):
    fights = []
    def fake_combat(player_data, enemy_name, group_size):
        fights.append((enemy_name, group_size))
        return result, 30, None
    monkeypatch.setattr("game.pyrpg.start_combat", fake_combat)
    monkeypatch.setattr(game, "auto_save_player_state", lambda: None)
    monkeypatch.setattr(game, "_process_level_ups", lambda: None)
    monkeypatch.setattr(game, "_roll_for_loot", lambda: None)
    return fights


def test_accepting_a_spawn_quest_starts_its_fight_and_winning_finishes_it(monkeypatch, tmp_path):
    use_quests(monkeypatch, tmp_path, [RAID])
    game = make_game()
    fights = stub_fights(monkeypatch, game)
    replies(monkeypatch, "1", "1")                 # open the raid, accept
    game.quest_board()
    assert fights == [("Townfolk", 3)]
    assert game.player_data.quest_flags["raid"] == 3


def test_a_spawn_quest_you_didnt_win_can_be_fought_again(monkeypatch, tmp_path):
    use_quests(monkeypatch, tmp_path, [RAID])
    game = make_game(accepted_quests=["raid"])
    fights = stub_fights(monkeypatch, game)
    replies(monkeypatch, "1", "1")                 # open, Fight
    game.quest_board()
    assert fights == [("Townfolk", 3)]


def test_quest_enemies_never_show_up_in_random_encounters():
    from enemies.enemies_data import get_encounter_weights
    names = {name.lower() for name, _ in get_encounter_weights(30)}
    assert "townfolk" not in names and "priest" not in names


def test_chain_quests_stay_hidden_until_the_earlier_one_is_done():
    game = make_game()
    assert "church_betrayal" not in [q for q, _ in game._visible_quests()]
    game.player_data.completed_quests.append("test_of_faith")
    assert "church_betrayal" in [q for q, _ in game._visible_quests()]


# --- fights out in the world ---------------------------------------------------------------

def test_victory_over_a_cat_updates_quest_progress(monkeypatch):
    game = make_game(accepted_quests=["lost_cat"])
    stub_fights(monkeypatch, game)
    monkeypatch.setattr("game.pyrpg.get_encounter_enemy", lambda power, depth=None: "Cat")
    monkeypatch.setattr("game.pyrpg.roll_group_size", lambda depth=0: 1)
    replies(monkeypatch)
    game.enter_combat()
    assert game.player_data.quest_flags.get("lost_cat") == 1


def test_a_group_victory_counts_every_enemy(monkeypatch, tmp_path):
    use_quests(monkeypatch, tmp_path, [WOLVES])
    game = make_game(accepted_quests=["wolves"])
    stub_fights(monkeypatch, game)
    monkeypatch.setattr("game.pyrpg.get_encounter_enemy", lambda power, depth=None: "Wolf")
    monkeypatch.setattr("game.pyrpg.roll_group_size", lambda depth=0: 3)
    replies(monkeypatch)
    game.enter_combat()
    assert game.player_data.quest_flags["wolves"] == 3


# --- saves -------------------------------------------------------------------------------

def test_quest_state_survives_save_and_load(monkeypatch, tmp_path):
    monkeypatch.setenv("PLAYERS_JSON", str(tmp_path / "players.json"))
    pd = PlayerData(name="QuestSaveTest", role="warrior", level=1, hp=30, stats=dict(STATS), max_hp=30,
                    quest_flags={"lost_wallet": 1}, completed_quests=["lost_wallet"], gold=30,
                    accepted_quests=["lost_wallet"], quest_choices={"lost_wallet": "Give"})
    put_new_player(Player(pd))

    loaded = get_player("QuestSaveTest")

    assert loaded.completed_quests == ["lost_wallet"]
    assert loaded.accepted_quests == ["lost_wallet"]
    assert loaded.quest_choices == {"lost_wallet": "Give"}


def test_old_saves_keep_the_quests_they_had_started(monkeypatch, tmp_path):
    import json
    save_path = tmp_path / "players.json"
    save_path.write_text(json.dumps({"players": [{
        "name": "OldSave", "role": "warrior", "level": 1, "hp": 30, "max_hp": 30, "stats": STATS,
        "quest_flags": {"pest_control": 2, "defeated_cat": True}, "completed_quests": ["spooky_area"],
    }]}))
    monkeypatch.setenv("PLAYERS_JSON", str(save_path))

    loaded = get_player("OldSave")

    assert set(loaded.accepted_quests) == {"spooky_area", "pest_control", "lost_cat"}


def test_old_saves_without_quest_fields_default_cleanly(monkeypatch, tmp_path):
    import json
    save_path = tmp_path / "players.json"
    save_path.write_text(json.dumps({"players": [{
        "name": "OldSave", "role": "warrior", "level": 1, "hp": 30, "max_hp": 30, "stats": STATS,
    }]}))
    monkeypatch.setenv("PLAYERS_JSON", str(save_path))

    loaded = get_player("OldSave")

    assert loaded.quest_flags == {} and loaded.completed_quests == [] and loaded.accepted_quests == []


def test_a_save_from_before_quests_csv_still_counts_as_done(monkeypatch):
    game = make_game(quest_flags={"defeated_cat": True}, accepted_quests=["lost_cat"])  # how Beta I saved a finished Lost Cat
    replies(monkeypatch, board_number(game, "lost_cat"), "1")
    game.quest_board()
    assert "lost_cat" in game.player_data.completed_quests


# --- "use" quests and perk rewards (Fast Travel System) -----------------------------------

def test_fast_travelling_completes_the_quest_and_the_perk_makes_the_next_trip_free(monkeypatch):
    game = make_game(depth_reached=10, gold=100, accepted_quests=["fast_travel_system"])
    number = board_number(game, "fast_travel_system")
    replies(monkeypatch, "10", "", number, "1", "", "", "10", "")  # travel, enter, open quest, claim, enter, leave, travel, enter

    game.fast_travel()                                    # paid trip: 25 gold, counts for the quest
    assert game.player_data.gold == 75
    assert game.player_data.quest_flags["fast_travel_system"] == 1

    game.player_data.in_town = True
    game.quest_board()
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


# --- reach quests and item rewards ---------------------------------------------------------

def test_exploring_to_depth_15_completes_the_reach_quest(monkeypatch):
    game = make_game(distance=14, accepted_quests=["spooky_area"])
    monkeypatch.setattr(PYRPG, "enter_combat", lambda self: None)
    monkeypatch.setattr(PYRPG, "passive_encounter", lambda self: False)
    game.explore()
    assert game.player_data.quest_flags["spooky_area"] == 1


def test_a_shallower_explore_does_not_count(monkeypatch):
    game = make_game(distance=5, accepted_quests=["spooky_area"])
    monkeypatch.setattr(PYRPG, "enter_combat", lambda self: None)
    monkeypatch.setattr(PYRPG, "passive_encounter", lambda self: False)
    game.explore()
    assert "spooky_area" not in game.player_data.quest_flags


def test_item_rewards_go_to_loot_so_the_voucher_works_in_the_shop(monkeypatch):
    game = make_game(quest_flags={"nasty_thieves": 2}, accepted_quests=["nasty_thieves"])
    replies(monkeypatch, board_number(game, "nasty_thieves"), "1")
    game.quest_board()
    assert "Voucher" in game.player_data.loot
    assert "voucher" not in game.player_data.perks


def test_a_voucher_stuck_in_perks_moves_to_loot_on_load():
    from util.file_io import _rescue_item_rewards
    assert _rescue_item_rewards(["voucher", "free_fast_travel"], ["Nuts"]) == (["free_fast_travel"], ["Nuts", "Voucher"])


# --- data/quests.csv ----------------------------------------------------------------------

def test_every_quest_in_the_csv_uses_a_type_the_game_handles():
    from quests.quests_data import get_quests, SUPPORTED_TYPES
    for quest_id, quest in get_quests().items():
        assert quest["type"] in SUPPORTED_TYPES, f"{quest_id}: unknown quest type {quest['type']!r}"


def test_every_quest_spawn_is_a_real_enemy():
    from enemies.enemies_data import get_enemy_stats
    from quests.quests_data import get_quests
    for quest_id, quest in get_quests().items():
        if quest["spawn"]:
            assert get_enemy_stats(quest["spawn"][0]), f"{quest_id}: no enemy called {quest['spawn'][0]!r}"


# --- Charisma ------------------------------------------------------------------------------

def test_charisma_sways_prices_both_ways_and_caps_at_15_percent():
    from util.charisma import charisma_price
    assert charisma_price(100, 0) == 100
    assert charisma_price(100, 10) == 96          # int(10 * 0.48) = 4% off
    assert charisma_price(100, -10) == 104
    assert charisma_price(100, 99) == 85 and charisma_price(100, -99) == 115


def test_the_shop_charges_the_charisma_price(monkeypatch):
    game = make_game(gold=100)
    game.player_data.stats["Charisma"] = 31        # 14% off
    replies(monkeypatch, "")
    assert game._buy("Health potion", 15, has_voucher=False)
    assert game.player_data.gold == 100 - 13


def test_charisma_doesnt_count_toward_encounter_power():
    game = make_game()
    before = game._player_power()
    game.player_data.stats["Charisma"] = 40
    assert game._player_power() == before
