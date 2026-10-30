from adventures.adventures import ADVENTURES, cave_entrance, parse_spawn, roll_spawn, strange_obelisk
from game.pyrpg import PYRPG
from players.player_data import PlayerData

STATS = {'Strength': 5, 'Agility': 5, 'Intelligence': 5, 'Defence': 5, 'Magic': 5, 'Luck': 5}
CAVE = {"Type": "Adventure", "Description": "Cave entrance", "Enemy_spawn": "Bear *2"}


def make_game():
    game = PYRPG.__new__(PYRPG)
    game.player_data = PlayerData(name="T", role="warrior", level=1, hp=99, stats=dict(STATS), max_hp=99)
    return game


def test_parse_spawn():
    assert parse_spawn("Bear *2") == ("Bear", 2)
    assert parse_spawn("Mimic") == ("Mimic", 1)
    assert parse_spawn("") is None


def test_walking_past_the_cave_does_nothing(monkeypatch):
    game = make_game()
    monkeypatch.setattr("builtins.input", lambda *_: "n")
    assert cave_entrance(game, CAVE) is None
    assert game.player_data.gold == 0


def test_the_cave_can_hold_the_spawn_group(monkeypatch):
    game = make_game()
    fights = []
    monkeypatch.setattr("builtins.input", lambda *_: "y")
    monkeypatch.setattr("adventures.adventures.random.choices", lambda seq, weights: ["bears"])
    monkeypatch.setattr(PYRPG, "fight", lambda self, enemy, size: fights.append((enemy, size)) or "victory")
    assert cave_entrance(game, CAVE) == "victory"
    assert fights == [("Bear", 2)]


def test_a_cave_chest_is_always_real(monkeypatch):
    game = make_game()
    monkeypatch.setattr("builtins.input", lambda *_: "y")
    monkeypatch.setattr("adventures.adventures.random.choices", lambda seq, weights: ["chest"])
    monkeypatch.setattr(PYRPG, "fight", lambda *_: (_ for _ in ()).throw(AssertionError("no fight")))
    monkeypatch.setattr(PYRPG, "_roll_for_loot", lambda self, source: None)
    assert cave_entrance(game, CAVE) == "chest"
    assert 5 <= game.player_data.gold <= 13


def test_every_adventure_and_event_in_the_csv_has_a_handler():
    from util.file_io import get_data, read_csv
    header, *rows = read_csv(get_data("encounters_csv"))
    type_col, desc_col = header.index("Type"), header.index("Description")
    for row in rows:
        if row and row[type_col] in ("Adventure", "Event"):
            assert row[desc_col] in ADVENTURES


# --- the strange obelisk -------------------------------------------------------------------------

OBELISK = {"Type": "Event", "Description": "A strange obelisk", "Enemy_spawn": "?x2"}


def test_a_strong_spawn_rolls_against_double_the_usual_target(monkeypatch):
    game = make_game()
    game.player_data.distance = 8
    asked = []
    monkeypatch.setattr("adventures.adventures.get_encounter_enemy",
                        lambda power, depth: asked.append((power, depth)) or "Bear")
    assert roll_spawn(game, "?x2") == ("Bear", 1)
    assert asked == [(game._player_power() * 2, 8)]
    assert roll_spawn(game, "Bear *2") == ("Bear", 2)          # named enemies are left alone


def test_the_obelisk_can_grant_a_full_level(monkeypatch):
    game = make_game()
    monkeypatch.setattr("builtins.input", lambda *_: "y")
    monkeypatch.setattr("adventures.adventures.random.choices", lambda seq, weights: ["exp"])
    monkeypatch.setattr(PYRPG, "_allocate_level_up_points", lambda self, points: None)
    assert strange_obelisk(game, OBELISK) == "exp"
    assert game.player_data.level == 2 and game.player_data.exp == 0


def test_the_obelisk_can_wake_something_strong(monkeypatch):
    game = make_game()
    fights = []
    monkeypatch.setattr("builtins.input", lambda *_: "y")
    monkeypatch.setattr("adventures.adventures.random.choices", lambda seq, weights: ["enemy"])
    monkeypatch.setattr("adventures.adventures.get_encounter_enemy", lambda power, depth: "Dragon")
    monkeypatch.setattr(PYRPG, "fight", lambda self, enemy, size: fights.append((enemy, size)) or "victory")
    assert strange_obelisk(game, OBELISK) == "victory"
    assert fights == [("Dragon", 1)]
    assert game.player_data.level == 1                          # no free level on this branch
