import csv
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


def get_data(node_name):
    env_key = node_name.upper()
    value = os.environ.get(env_key)

    if value is None:
        raise ValueError(f"No '{env_key}' entry found in {_env_path}")

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


def check_existing_player(player_name):
    players_csv_path = get_data("players_csv")
    csv_data = read_csv(players_csv_path)

    headers = csv_data[0]  # ['name', 'role', 'level', 'HP', 'strength', ...]
    stat_keys = headers[4:]

    for row in csv_data[1:]:
        if row and row[0].strip().lower() == player_name.strip().lower():
            role = row[1]
            level = int(row[2])
            hp = float(row[3])
            stats = {stat_keys[i]: int(row[i + 4]) for i in range(len(stat_keys))}
            return PlayerData(name=player_name, role=role, level=level, hp=hp, stats=stats)

    return None
