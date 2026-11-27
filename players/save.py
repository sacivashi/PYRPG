from dataclasses import asdict

from players.player_data import saved_fields
from players.profiles import save_adventurer


def put_new_player(new_player_obj, quiet=False):
    """Save an adventurer under the active player (replacing their save if it already exists)"""
    player_data = new_player_obj.player_data()
    name = player_data.name.title()  # Normalize name case

    # every saved PlayerData field, so new fields save automatically (effects never do)
    everything = asdict(player_data)
    entry = {f.name: everything[f.name] for f in saved_fields()}
    entry.update(name=name, hp=int(player_data.hp), max_hp=int(player_data.max_hp))
    save_adventurer(entry)

    if not quiet:
        print(f"Saved {name}.")
