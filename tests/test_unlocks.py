"""v1.0.7 unlocks: shared progress, what each row type counts, and what stays locked until earned"""
import json

from combat.combat import Combat, start_combat
from game.pyrpg import PYRPG
from players.player_data import PlayerData
from unlocks import unlocks
from unlocks.unlocks import (check_state, grant, is_unlocked, journal_lines, load_progress, locked_names,
                             locked_role_lines, record)

STATS = {'Strength': 5, 'Agility': 5, 'Intelligence': 0, 'Charisma': 0, 'Defense': 5, 'Magic': 5, 'Luck': 5}
HEADER = "id,unlocks,type,target,amount,role,hint"


def use_rows(monkeypatch, tmp_path, *rows):
    path = tmp_path / "unlocks_rows.csv"
    path.write_text(HEADER + "\n" + "\n".join(rows) + "\n")
    monkeypatch.setenv("unlocks_csv", str(path))


def make_game(**overrides):
    game = PYRPG.__new__(PYRPG)
    defaults = dict(name="T", role="warrior", level=1, hp=40, stats=dict(STATS), max_hp=40)
    defaults.update(overrides)
    game.player_data = PlayerData(**defaults)
    return game


def replies(monkeypatch, *answers):
    it = iter(answers)
    monkeypatch.setattr("builtins.input", lambda *_: next(it, ""))


# --- the real unlocks.csv ----------------------------------------------------------------------

def test_everything_named_in_unlocks_csv_exists():
    from enemies.enemies_data import get_enemy_stats
    from items.items_data import get_item_names
    from roles.roles_data import RolesExtract
    roles = set(RolesExtract.get_role_names())
    items = {name.lower() for name in get_item_names()}
    for row in unlocks.get_unlock_rows():
        category, name = row["unlocks"].split(":", 1)
        assert {"class": name in roles, "enemy": get_enemy_stats(name) is not None,
                "item": name.lower() in items, "event": True}[category], row["id"]


def test_a_fresh_game_has_the_unlockables_locked():
    assert locked_names("class") == {"knight", "monk", "necromancer", "forsaken", "tank"}
    assert locked_names("enemy") == {"cursed human", "cursed priest", "vampire lord", "behemoth"}
    assert locked_names("item") == {"necronomicon", "overflow charm", "void shard", "hunter's trophy"}
    assert not is_unlocked("event:Halt!")
    assert is_unlocked("class:mage")            # not named by any row: never locked


def test_locked_enemies_and_items_never_show_up():
    from enemies.enemies_data import get_encounter_weights
    from items.items_data import get_droppable_items
    names = {name for name, _ in get_encounter_weights(50)}
    assert "Cursed Human" not in names and "Behemoth" not in names
    assert "Necronomicon" not in {name for name, _ in get_droppable_items()}
    grant("enemy:Cursed Human")
    grant("item:Necronomicon")
    assert "Cursed Human" in {name for name, _ in get_encounter_weights(50)}
    assert "Necronomicon" in {name for name, _ in get_droppable_items()}


def test_locked_classes_cant_be_picked(monkeypatch, capsys):
    from roles.input_role import InputRole
    replies(monkeypatch, "knight", "mage", "y")
    assert InputRole.choose_role() == "mage"
    out = capsys.readouterr().out
    assert "Locked:" in out and "???  Complete 5 quests that gain charisma" in out
    assert "As a mage, defeat 15 enemies with -lck   (0/15)" in out


# --- counting ----------------------------------------------------------------------------------

def test_progress_is_saved_and_shared(monkeypatch, tmp_path):
    use_rows(monkeypatch, tmp_path, "z,item:Thing,defeat,Zombie,6,,Beat zombies")
    record("defeat", "Zombie", 4)
    record("defeat", "zombie", 1)
    assert load_progress()["progress"] == {"z": 5}
    assert record("defeat", "Zombie", 3) == ["item:Thing"]      # unlocking says so once...
    assert record("defeat", "Zombie", 3) == []                  # ...and stops counting
    with open(unlocks._path(), encoding="utf-8") as file:
        assert json.load(file)["unlocked"] == ["item:Thing"]


def test_role_rows_only_count_for_that_role(monkeypatch, tmp_path):
    use_rows(monkeypatch, tmp_path, "n,class:x,defeat,-lck,2,Mage,Defeat")
    record("defeat", "Zombie", 1, role="warrior")
    record("defeat", "Wolf", 1, role="mage")        # Luck 17: doesn't count
    assert load_progress()["progress"] == {}
    record("defeat", "Zombie", 2, role="mage")      # Luck -2
    assert is_unlocked("class:x")


def test_any_row_unlocks_it(monkeypatch, tmp_path):
    use_rows(monkeypatch, tmp_path, "a,class:x,defeated,,20,,Die a lot",
             "b,class:x,stat_above,Defense,10,,Get tanky")
    assert check_state("warrior", stats={"Defense": 9}) == []
    assert check_state("warrior", stats={"Defense": 10}) == ["class:x"]


def test_the_same_enemy_counts_per_enemy(monkeypatch, tmp_path):
    use_rows(monkeypatch, tmp_path, "t,item:Trophy,encounter,,3,,Same enemy 3 times")
    for name in ("Wolf", "Wolf", "Bat", "Bat"):
        record("encounter", name)
    assert not is_unlocked("item:Trophy")
    record("encounter", "Bat")
    assert is_unlocked("item:Trophy")


def test_thresholds(monkeypatch, tmp_path):
    use_rows(monkeypatch, tmp_path, "a,class:a,equip,Necronomicon,1,Mage,Equip it",
             "b,class:b,stat_below,Magic,0,Warrior,No magic",
             "c,enemy:C,max_hp,,100,,Big",
             "d,enemy:D,quest,townfolk_raid,1,,Raid")
    assert check_state("warrior", "Necronomicon", {"Magic": 1}, 99, ["lost_cat"]) == []
    assert set(check_state("mage", "necronomicon", {"Magic": 0}, 100, ["townfolk_raid"])) == {"class:a", "enemy:C", "enemy:D"}
    assert check_state("warrior", None, {"Magic": 0}) == ["class:b"]


def test_quiet_unlocks(monkeypatch, tmp_path, capsys):
    use_rows(monkeypatch, tmp_path, "a,class:knight,defeated,,1,,x", "b,enemy:Behemoth,defeated,,1,,y")
    record("defeated")
    out = capsys.readouterr().out
    assert "✦ Unlocked: Knight ✦" in out
    assert "...something followed you out of town." in out and "Behemoth" not in out


# --- where the game reports it ---------------------------------------------------------------------

def test_wins_losses_and_prayers_are_reported(monkeypatch, tmp_path):
    use_rows(monkeypatch, tmp_path, "z,item:A,defeat,Zombie,6,,x", "d,item:B,defeated,,20,,y",
             "p,item:C,use,Sculpture,20,,z")
    game = make_game()
    game.events.emit("victory", enemy="Zombie", size=3)
    game.events.emit("defeated", enemy="Wolf")
    game.events.emit("prayed")
    assert load_progress()["progress"] == {"z": 3, "d": 1, "p": 1}


def test_praying_counts_for_test_of_faith(monkeypatch):
    from adventures.encounters import sculpture
    game = make_game(accepted_quests=["test_of_faith"])
    replies(monkeypatch, "y", "")
    monkeypatch.setattr("adventures.encounters.random.randint", lambda a, b: 1)   # the gods don't answer
    sculpture(game, {})
    assert game.player_data.quest_flags["test_of_faith"] == 1


def test_charisma_quests_count(monkeypatch, tmp_path):
    use_rows(monkeypatch, tmp_path, "k,class:knight,charisma_quest,,5,,Nice")
    game = make_game(accepted_quests=["lost_wallet"], quest_flags={"lost_wallet": 1})
    from quests.quests_data import get_quests
    replies(monkeypatch, "2", "")                     # Take wallet: -3 Charisma
    game._complete_quest("lost_wallet", get_quests()["lost_wallet"])
    assert load_progress()["progress"] == {}
    game = make_game(accepted_quests=["lost_wallet"], quest_flags={"lost_wallet": 1})
    replies(monkeypatch, "1", "")                     # Give: +1
    game._complete_quest("lost_wallet", get_quests()["lost_wallet"])
    assert load_progress()["progress"] == {"k": 1}


def test_combat_tallies(monkeypatch, tmp_path):
    use_rows(monkeypatch, tmp_path, "b,item:A,block,,1000,,x", "m,item:B,mana_spent,,1000,,y",
             "e,item:C,encounter,Weakling,1000,,z")
    pd = PlayerData(name="T", role="mage", level=1, hp=40, stats=dict(STATS), max_hp=40,
                    known_spells=["Light shock"], in_town=False, distance=1)
    replies(monkeypatch, "2", "1", "1")              # cast the first spell, then attack until it's over
    start_combat(pd, "Weakling")
    progress = load_progress()["progress"]
    assert progress["e"] == 1 and progress["m"] > 0


def test_defending_counts_blocked_damage():
    combat = Combat(make_game(stats=dict(STATS, Defense=10)).player_data, "Bear")
    combat.defending = True
    combat.enemy_attack(combat.enemies[0])
    assert combat.tally["block"] >= 0


def test_curses_bringing_a_stat_to_0_count():
    combat = Combat(make_game().player_data, "Weakling")
    enemy = combat.enemies[0]
    enemy.stats = {"Attack": 2, "Speed": 0, "Defense": 0, "Luck": 0}
    combat.apply_debuff_to_enemy(enemy, 5)
    assert enemy.stats["Attack"] == 0 and combat.tally["zeroed"] == 1


# --- the Journal ---------------------------------------------------------------------------------------

def test_journal(monkeypatch, tmp_path, capsys):
    use_rows(monkeypatch, tmp_path, "a,class:knight,defeated,,20,,Be defeated 20 times",
             "b,enemy:Behemoth,max_hp,,100,,Reach a max HP of 100",
             "c,enemy:Cursed Human,defeated,,1,,Lose once")
    record("defeated", amount=7)
    lines = journal_lines()
    assert lines[1] == "Classes   0/1   Enemies   1/2"
    assert any("Be defeated 20 times   (7/20)" in line for line in lines)
    assert any(line.strip().startswith("Cursed Human") and "unlocked" in line for line in lines)
    game = make_game(quest_choices={"lost_wallet": "Give"})
    replies(monkeypatch, "")
    game.journal()
    assert "Lost Wallet" in capsys.readouterr().out


def test_locked_role_lines(monkeypatch, tmp_path):
    use_rows(monkeypatch, tmp_path, "a,class:x,defeated,,20,,Be defeated 20 times")
    record("defeated", amount=7)
    assert locked_role_lines() == ["  ???  Be defeated 20 times   (7/20)"]
