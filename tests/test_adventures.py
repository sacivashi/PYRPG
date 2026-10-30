from adventures.adventures import ADVENTURES, cave_entrance, parse_spawn
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


def test_every_adventure_in_the_csv_has_a_handler():
    from util.file_io import get_data, read_csv
    header, *rows = read_csv(get_data("encounters_csv"))
    type_col, desc_col = header.index("Type"), header.index("Description")
    for row in rows:
        if row and row[type_col] == "Adventure":
            assert row[desc_col] in ADVENTURES
