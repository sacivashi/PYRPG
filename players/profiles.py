"""Players (v1.1.1): the person playing, who owns adventurers and unlock progress.

data/players.json:
    {"Players": {"Raz": {"Adventurers": [{...PlayerData...}, ...],
                         "Unlocks": {"progress": {...}, "unlocked": [...]}}}}

Player and adventurer names aren't case sensitive: they're found whatever the case, and always
shown the way they were first written. Two players can each have an adventurer called Bee.

ACTIVE is the player currently playing (set by the start menu). Saves, loads and unlock progress
all go to them. With nobody active, unlock progress is kept in memory only.

Saves from before players existed ({"players": [...]}) are moved aside, never read:
archive_old_saves() renames them to players_old.json, along with the old shared unlocks.json.
"""
import os

from util.file_io import get_data, read_json, write_json

ACTIVE = None
_memory_unlocks = {}


def set_active(name):
    global ACTIVE
    ACTIVE = name


def _path():
    return get_data("players_json")


def load_all():
    """{stored name: profile}. An old-format or missing file reads as no players."""
    data = read_json(_path()) if os.path.exists(_path()) else {}
    players = data.get("Players") if isinstance(data, dict) else None
    return players if isinstance(players, dict) else {}


def _write_all(players):
    write_json(_path(), {"Players": players})


def find_player(name):
    """The stored spelling of a player name, or None"""
    wanted = (name or "").strip().lower()
    return next((stored for stored in load_all() if stored.lower() == wanted), None)


def create_player(name):
    """Make a new, empty player and return their stored name (the existing one if taken)"""
    existing = find_player(name)
    if existing:
        return existing
    players = load_all()
    name = name.strip()
    players[name] = {"Adventurers": [], "Unlocks": {"progress": {}, "unlocked": []}}
    _write_all(players)
    return name


def _profile(players, name):
    stored = next((key for key in players if key.lower() == (name or "").lower()), name)
    return players.setdefault(stored, {"Adventurers": [], "Unlocks": {"progress": {}, "unlocked": []}})


def adventurer_entries(player=None):
    """The raw saved adventurers (dicts) of a player, the active one by default"""
    player = player or ACTIVE
    stored = find_player(player) if player else None
    if not stored:
        return []
    return list(load_all()[stored].get("Adventurers", []))


def save_adventurer(entry, player=None):
    """Add or replace (same name, any case) one adventurer under a player"""
    players = load_all()
    adventurers = _profile(players, player or ACTIVE).setdefault("Adventurers", [])
    for i, saved in enumerate(adventurers):
        if saved["name"].lower() == entry["name"].lower():
            adventurers[i] = entry
            break
    else:
        adventurers.append(entry)
    _write_all(players)


def delete_adventurer(name, player=None):
    players = load_all()
    stored = find_player(player or ACTIVE)
    if not stored:
        return False
    adventurers = players[stored].get("Adventurers", [])
    for i, saved in enumerate(adventurers):
        if saved["name"].strip().lower() == name.strip().lower():
            del adventurers[i]
            _write_all(players)
            return True
    return False


# --- unlock progress ---------------------------------------------------------------------------

def load_unlocks():
    if ACTIVE is None:
        data = _memory_unlocks
    else:
        stored = find_player(ACTIVE)
        data = load_all()[stored].get("Unlocks", {}) if stored else {}
    data = data if isinstance(data, dict) else {}
    data.setdefault("progress", {})
    data.setdefault("unlocked", [])
    return data


def save_unlocks(data):
    if ACTIVE is None:
        _memory_unlocks.clear()
        _memory_unlocks.update(data)
        return
    players = load_all()
    _profile(players, ACTIVE)["Unlocks"] = data
    _write_all(players)


# --- saves from before players --------------------------------------------------------------------

def _free_name(path):
    """path, or path with " (2)", " (3)"... before the extension if that's taken"""
    base, ext = os.path.splitext(path)
    candidate, n = path, 2
    while os.path.exists(candidate):
        candidate, n = f"{base} ({n}){ext}", n + 1
    return candidate


def archive_old_saves():
    """Move pre-1.1.1 save files aside (players_old.json, unlocks_old.json).
    Returns the new paths, empty if there was nothing to move."""
    moved = []
    players_path = _path()
    if os.path.exists(players_path):
        try:
            data = read_json(players_path)
        except ValueError:
            data = {"players": "unreadable"}
        if isinstance(data, dict) and "Players" not in data and data.get("players"):
            moved.append(_free_name(players_path.replace(".json", "_old.json")))
            os.rename(players_path, moved[-1])
    unlocks_path = get_data("unlocks_json")
    if os.path.exists(unlocks_path):
        moved.append(_free_name(unlocks_path.replace(".json", "_old.json")))
        os.rename(unlocks_path, moved[-1])
    return moved
