import csv
import json
import os
from players.player_data import PlayerData

# Navigate from util/file_io.py up to the project root
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_env_path = os.path.join(_project_root, ".env")


def _load_env_file():
    if not os.path.exists(_env_path):
        return

    with open(_env_path, encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)


_load_env_file()


def _get_config_value(node_name):
    candidates = [node_name, node_name.upper(), node_name.lower()]
    for key in candidates:
        if os.environ.get(key):
            return os.environ.get(key)

    defaults = {
        "roles_csv": "data/roles.csv",
        "enemies_csv": "data/enemies.csv",
        "players_json": "data/players.json",
    }
    return defaults.get(node_name.lower())


def get_data(node_name):
    value = _get_config_value(node_name)

    if value is None:
        raise ValueError(f"No '{node_name}' entry found in {_env_path}")

    if os.path.isabs(value):
        return value

    return os.path.join(_project_root, value)


def read_csv(file_name):
    data = []
    with open(file_name, newline='', encoding='utf-8') as file:
        reader = csv.reader(file)
        for row in reader:
            data.insert(len(data), row)
        return data


def read_json(file_name):
    if not os.path.exists(file_name):
        return {"players": []}

    with open(file_name, encoding="utf-8") as file:
        return json.load(file)


def write_json(file_name, data):
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def get_player(player_name):
    players_json_path = get_data("players_json")
    data = read_json(players_json_path)

    for player in data["players"]:
        if player["name"].strip().lower() == player_name.strip().lower():
            return PlayerData(
                name=player["name"],
                role=player["role"],
                level=player["level"],
                hp=player["hp"],
                stats=player["stats"],
                max_hp=player.get("max_hp"),  # None for saves predating max_hp tracking
            )

    return None


def delete_player(player_name):
    players_json_path = get_data("players_json")
    data = read_json(players_json_path)

    for i, player in enumerate(data["players"]):
        if player["name"].strip().lower() == player_name.strip().lower():
            del data["players"][i]
            write_json(players_json_path, data)
            return True

    return False
