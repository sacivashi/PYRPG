from dataclasses import fields

from combat.combat_player import Player
from players.player_data import PlayerData
from players.save import put_new_player
from util.file_io import get_player

STATS = {'Strength': 5, 'Agility': 5, 'Intelligence': 5, 'Defense': 5, 'Magic': 5, 'Luck': 5}


def test_every_player_data_field_survives_combat_and_save(monkeypatch, tmp_path):
    """A new PlayerData field should need no wiring anywhere else — if this fails after adding
    one, something is still copying fields by hand."""
    monkeypatch.setenv("PLAYERS_JSON", str(tmp_path / "players.json"))
    (tmp_path / "players.json").write_text('{"players": []}')
    original = PlayerData(name="Roundtrip", role="warrior", level=4, hp=20, stats=dict(STATS), mana=10,
                          gold=42, loot=["Nuts"], equipped="Dagger", exp=37, in_town=False, distance=9,
                          depth_reached=12, failed_attempts=2, quest_flags={"lost_cat": 1},
                          completed_quests=["charity"], known_spells=["Fireball"],
                          item_state={"Thunder apprentice": 3}, perks=["free_fast_travel"])

    put_new_player(Player(original))
    loaded = get_player("Roundtrip")

    for f in fields(PlayerData):
        if f.name != "max_hp":  # recomputed from stats + gear
            assert getattr(loaded, f.name) == getattr(original, f.name), f.name
