from combat.combat_player import Player
from game.pyrpg import PYRPG
from players.player_data import PlayerData
from players.save import put_new_player
from util.file_io import get_player

STATS = {'Strength': 5, 'Agility': 5, 'Intelligence': 5, 'Defence': 5, 'Magic': 5, 'Luck': 5}
FIXED_ROLL = {'Strength': 3, 'Agility': -5, 'Intelligence': 0, 'Defence': 4, 'Magic': -2, 'Luck': 5}


def make_player_data(**overrides):
    return PlayerData(name="T", role="warrior", level=1, hp=30, stats=dict(STATS), max_hp=30, **overrides)


def make_game(**overrides):
    game = PYRPG.__new__(PYRPG)
    game.player_data = make_player_data(**overrides)
    return game


def test_roll_is_one_delta_per_stat_within_minus_5_to_5():
    for _ in range(200):
        roll = Player.roll_dice_machine()
        assert set(roll) == set(STATS)
        assert all(-5 <= delta <= 5 for delta in roll.values())


def test_apply_equipment_uses_exactly_the_stored_roll():
    effective = Player.apply_equipment(STATS, "Dice machine", FIXED_ROLL)
    assert effective == {stat: STATS[stat] + FIXED_ROLL[stat] for stat in STATS}


def test_effective_stats_are_stable_across_repeated_calls():
    game = make_game(equipped="Dice machine", dice_roll=dict(FIXED_ROLL))
    first = game._effective_stats()
    assert all(game._effective_stats() == first for _ in range(20))


def test_first_equip_rolls_and_stores_once():
    game = make_game(equipped="Dice machine")
    assert game.player_data.dice_roll is None
    game._ensure_dice_roll()
    stored = dict(game.player_data.dice_roll)
    for _ in range(20):
        game._ensure_dice_roll()
    assert game.player_data.dice_roll == stored


def test_unequipping_and_reequipping_does_not_reroll():
    game = make_game(equipped="Dice machine")
    game._ensure_dice_roll()
    stored = dict(game.player_data.dice_roll)
    game.player_data.equipped = None
    game._ensure_dice_roll()
    game.player_data.equipped = "Dice machine"
    game._ensure_dice_roll()
    assert game.player_data.dice_roll == stored


def test_no_roll_is_made_for_other_gear_or_nothing():
    for equipped in (None, "Iron Sword"):
        game = make_game(equipped=equipped)
        game._ensure_dice_roll()
        assert game.player_data.dice_roll is None


def test_player_keeps_a_stored_roll_so_combat_matches_the_menus():
    player = Player(make_player_data(equipped="Dice machine", dice_roll=dict(FIXED_ROLL)))
    assert player.stats == {stat: STATS[stat] + FIXED_ROLL[stat] for stat in STATS}
    assert player.base_stats == STATS  # gear never leaks into the saved base stats
    assert player.player_data().dice_roll == FIXED_ROLL


def test_player_rolls_once_when_worn_without_a_roll_and_hands_it_back():
    player = Player(make_player_data(equipped="Dice machine"))
    rolled = player.player_data().dice_roll
    assert rolled is not None and set(rolled) == set(STATS)
    assert player.stats == {stat: STATS[stat] + rolled[stat] for stat in STATS}


def test_roll_survives_a_save_and_load(tmp_path, monkeypatch):
    monkeypatch.setenv("PLAYERS_JSON", str(tmp_path / "players.json"))  # never touch the real save file
    put_new_player(Player(make_player_data(equipped="Dice machine", dice_roll=dict(FIXED_ROLL))))
    loaded = get_player("T")
    assert loaded.dice_roll == FIXED_ROLL
    assert loaded.equipped == "Dice machine"
    assert loaded.stats == STATS
