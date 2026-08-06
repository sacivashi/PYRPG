from util.file_io import get_data, read_json, write_json


def put_new_player(new_player_obj):
    players_json_path = get_data("players_json")
    data = read_json(players_json_path)

    player_data = new_player_obj.player_data()
    name = player_data.name.title()  # Normalize name case

    new_entry = {
        "name": name,
        "role": player_data.role,
        "level": player_data.level,
        "hp": int(player_data.hp),
        "stats": player_data.stats,
    }

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

    print(f"Player '{name}' {'updated' if found else 'saved'} successfully!")
