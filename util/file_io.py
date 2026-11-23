import csv
import json
import os
from players.player_data import PlayerData, saved_fields

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
        "items_csv": "data/items.csv",
        "quests_csv": "data/quests.csv",
        "encounters_csv": "data/encounters.csv",
        "unlocks_csv": "data/unlocks.csv",
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
    """Every row as a dict keyed by the header, e.g. row["Defense"] — columns are found by name,
    so adding or reordering columns never shifts the others. Blank lines are skipped."""
    with open(file_name, newline='', encoding='utf-8') as file:
        return [row for row in csv.DictReader(file) if any(cell and cell.strip() for cell in row.values())]


def read_json(file_name):
    if not os.path.exists(file_name):
        return {"players": []}

    with open(file_name, encoding="utf-8") as file:
        content = file.read().strip()

    if not content:
        return {"players": []}

    return json.loads(content)


def write_json(file_name, data):
    with open(file_name, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def _migrate_stats(stats, role=None):
    """Old saves: read the pre-rename Defence key as Defense, and give characters from before
    Charisma existed their class's Charisma (placed in roles.csv's column order, so it shows up
    in the same spot as on a new character)."""
    if "Defence" in stats:
        stats = {("Defense" if k == "Defence" else k): v for k, v in stats.items()}
    from util.charisma import CHARISMA
    if CHARISMA not in stats:
        from roles.roles_data import RolesExtract
        role_stats = RolesExtract.get_role_stats_by_name().get((role or "").lower(), {})
        stats = {**stats, CHARISMA: role_stats.get(CHARISMA, 0)}
        order = list(role_stats)
        if order:
            stats = {k: stats[k] for k in sorted(stats, key=lambda k: order.index(k) if k in order else len(order))}
    return stats


def _rescue_item_rewards(perks, loot):
    """Quest item rewards (e.g. the Nasty Thieves voucher) used to be filed under perks, where
    nothing ever used them — move them into loot. Returns (perks, loot)."""
    from quests.quests_data import reward_item
    items = [reward_item(perk) for perk in perks]
    return ([perk for perk, item in zip(perks, items) if not item],
            loot + [item for item in items if item])


def get_player(player_name):
    players_json_path = get_data("players_json")
    data = read_json(players_json_path)

    for player in data["players"]:
        if player["name"].strip().lower() == player_name.strip().lower():
            # every field the save has; anything missing (older saves) gets the PlayerData default
            saved = {f.name: player[f.name] for f in saved_fields() if f.name in player}
            saved.setdefault("depth_reached", player.get("distance", 0))  # older saves: start from where they are
            saved["stats"] = _migrate_stats(saved["stats"], saved.get("role"))
            saved["perks"], saved["loot"] = _rescue_item_rewards(saved.get("perks", []), saved.get("loot", []))
            if "accepted_quests" not in player:  # from before quests were opt-in
                from quests.quests_data import started_quests
                saved["accepted_quests"] = started_quests(saved.get("completed_quests", []),
                                                          saved.get("quest_flags", {}))
            return PlayerData(**saved)

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
