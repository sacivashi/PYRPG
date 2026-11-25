from dataclasses import asdict

from players.player_data import saved_fields

from util.file_io import get_data, read_json, write_json


def put_new_player(new_player_obj, quiet=False):
    players_json_path = get_data("players_json")
    data = read_json(players_json_path)

    player_data = new_player_obj.player_data()
    name = player_data.name.title()  # Normalize name case

    # every saved PlayerData field, so new fields save automatically (effects never do)
    everything = asdict(player_data)
    new_entry = {f.name: everything[f.name] for f in saved_fields()}
    new_entry.update(name=name, hp=int(player_data.hp), max_hp=int(player_data.max_hp))

    # Find existing player entry (if exists), else append
    found = False
    for i, player in enumerate(data["players"]):
        if player["name"].lower() == name.lower():
            data["players"][i] = new_entry
            found = True
            break

    if not found:
        data["players"].append(new_entry)

    write_json(players_json_path, data)

    if not quiet:
        print(f"Saved {name}.")
