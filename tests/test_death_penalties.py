from game.pyrpg import PYRPG
from players.player_data import PlayerData

STATS = {'Strength': 9, 'Agility': 5, 'Intelligence': 10, 'Defence': 8, 'Magic': 2, 'Luck': 4}


def make_game(**overrides):
    game = PYRPG.__new__(PYRPG)
    defaults = dict(name="T", role="warrior", level=1, hp=5, stats=dict(STATS), max_hp=26,
                    gold=100, exp=60.0, mana=3)
    defaults.update(overrides)
    game.player_data = PlayerData(**defaults)
    return game


def never_lose_items(monkeypatch):
    monkeypatch.setattr("game.pyrpg.random.randint", lambda a, b: 100)


def always_lose_items(monkeypatch):
    monkeypatch.setattr("game.pyrpg.random.randint", lambda a, b: 1)


def test_death_costs_15_percent_of_gold(monkeypatch):
    never_lose_items(monkeypatch)
    game = make_game(gold=100)
    game._apply_death_penalties()
    assert game.player_data.gold == 85


def test_death_costs_20_percent_of_exp_progress_without_dropping_a_level(monkeypatch):
    never_lose_items(monkeypatch)
    game = make_game(exp=60.0, level=3)
    game._apply_death_penalties()
    assert game.player_data.exp == 48.0
    assert game.player_data.level == 3


def test_resurrects_at_half_hp_and_30_percent_mana(monkeypatch):
    never_lose_items(monkeypatch)
    game = make_game()
    game._apply_death_penalties()
    assert game.player_data.hp == 13                    # 50% of 26
    assert game.player_data.mana == 13                  # 30% of 45 (Int 10 * 4.5)


def test_no_item_is_lost_when_the_roll_misses(monkeypatch):
    never_lose_items(monkeypatch)
    game = make_game(loot=["Bomb", "Dagger"])
    game._apply_death_penalties()
    assert game.player_data.loot == ["Bomb", "Dagger"]


def test_a_lost_equipped_item_gets_unequipped_and_max_hp_recomputed(monkeypatch):
    always_lose_items(monkeypatch)
    monkeypatch.setattr("game.pyrpg.random.choice", lambda items: "Turtle Shell")
    game = make_game(loot=["Turtle Shell"], equipped="Turtle Shell", max_hp=54)
    game._apply_death_penalties()
    assert game.player_data.loot == []
    assert game.player_data.equipped is None
    assert game.player_data.max_hp == 26                # back to un-geared max
    assert game.player_data.hp == 13                    # 50% of the post-loss max, not of 54


def test_losing_one_copy_of_an_equipped_item_keeps_it_equipped(monkeypatch):
    always_lose_items(monkeypatch)
    monkeypatch.setattr("game.pyrpg.random.choice", lambda items: "Dagger")
    game = make_game(loot=["Dagger", "Dagger"], equipped="Dagger")
    game._apply_death_penalties()
    assert game.player_data.loot == ["Dagger"]
    assert game.player_data.equipped == "Dagger"


def test_empty_loot_never_errors(monkeypatch):
    always_lose_items(monkeypatch)
    game = make_game(loot=[])
    game._apply_death_penalties()
    assert game.player_data.loot == []
