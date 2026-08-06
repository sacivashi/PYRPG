# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Game

```bash
python main.py
```

Must be run from the project root — imports are root-relative.

## Running Tests

There is currently no test suite. Testing is manual (`python main.py` and play through it).

## Architecture

### Data Flow

```
main.py
  └── game/pyrpg.py (PYRPG class)
        ├── players/input_name.py (InputName.input_name() — player creation / load)
        ├── combat/combat.py (Combat class, start_combat())
        └── players/save.py (put_new_player())
```

### Path Registry Pattern

CSV file paths resolve through `util/file_io.py`'s `get_data(node_name)`. Code never hard-codes paths. Resolution order:
1. An environment variable matching `node_name` (tried as-is, upper, and lower case)
2. A hardcoded default in `file_io.py`'s `_get_config_value()` (`roles_csv`, `enemies_csv`, `players_csv` → `data/*.csv`)

`get_data()` reads env vars via `os.environ`, which `_load_env_file()` populates from a `.env` file at the **project root** (`PYRPG/.env`), if one exists. Note: `data/.env` also exists in the repo but is *not* the file that gets loaded — it currently has no effect and the code runs on the hardcoded defaults instead, which happen to match its values.

```python
# util/file_io.py
def get_data(node_name):   # resolves path from env var or default, returns absolute path
def read_csv(file_name):   # returns list of rows (list of lists) — roles/enemies data
def read_json(file_name) / write_json(file_name, data)  # player save data
def get_player(player_name):  # checks data/players.json, returns PlayerData or None
def delete_player(player_name):  # removes a player entry, returns True/False
```

### Player Data

Player data flows as the `PlayerData` dataclass (`players/player_data.py`: `name, role, level, hp, stats, max_hp`) everywhere in the active game flow — both `NewPlayer.player_data()` and `get_player()` return one. `combat_player.py`'s `Player.__init__` also accepts a raw `(name, role, level, hp, stats)` tuple for backward compatibility, but nothing in the current flow produces one anymore.

### Combat System

`combat/combat.py` — `Combat` class manages one encounter. `start_combat(player_data, enemy_name)` is the public entry point.

`combat/damage_calculator.py` — `DamageCalculator` contains all stat-based formulas as static methods. Every formula maps directly to the Alpha II patch notes spec in `patch_notes/Alpha II.md`.

`combat/combat_player.py` — `Player` wraps player data for live HP tracking during combat. Stats and max HP are snapshotted at combat start and restored after (combat mutations don't persist).

### Negative Stat System

The core mechanic. Any stat can be negative. Each negative stat gives a debuff + a compensating benefit:

| Stat | Debuff | Benefit |
|------|--------|---------|
| -Strength | Self-damage after attacking | Heal on hit: `int(sqrt(missing_hp + damage_done) + abs(-str * 1.5))` |
| -Agility | Always acts last | `+min(35, abs(-agi))%` dodge/counter rate |
| -Intelligence | `min(50, abs(-int)+5)%` confusion chance | Hit harder: `2*abs(-int) - (highest_stat/10)` bonus |
| -Defence | Takes extra `abs(-def)` damage | Reflects `int((damage*1.5 + abs(-def)) / 2.5)` back |
| -Magic | Drains `abs(-mag)%` MAX HP on magic attack | `min(65, int(sqrt(abs(-mag))*10))%` chance to debuff enemy stat |
| -Luck | `min(35, abs(-lck))%` miss chance | Successful attacks are unavoidable |

Enemies have a parallel negative-stat system documented in `patch_notes/Alpha II.md`. Notably, enemies with negative HP use a **Corruption** mechanic: the enemy takes cumulative damage each turn (`corruption_counter += corruption` per turn), and player hits heal it.

### Role and Enemy Stats

- Roles: `data/roles.csv` — columns: `Class, Strength, Agility, Intelligence, Defence, Magic, Luck`
- Enemies: `data/enemies.csv` — columns: `Name, Corruption, HP, Attack, Defense, Speed, Luck`
- Save data: `data/players.json` (gitignored) — `{"players": [{"name", "role", "level", "hp", "max_hp", "stats"}, ...]}`. `max_hp` is optional for backward compatibility with older saves (`None` if absent); when present, it lets `Player` detect max_hp increases (formula tweaks, stat changes) on load and heal the character by the difference instead of leaving them stranded below the new cap.

Roles/enemies stats are read via `RolesExtract` (`roles/roles_data.py`) and `get_enemy_stats()` (`enemies/enemies_data.py`), both built on `get_data()` + `read_csv()`. Player saves use `get_data()` + `read_json()`/`write_json()` instead (`util/file_io.py`).

### HP Formula

Player HP = `max(22, abs(Strength) * 0.95 + abs(Defence) * 2.3)` — `Player.calculate_hp()` in `combat/combat_player.py`, used for both new and loaded players.
