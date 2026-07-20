# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Game

```bash
python main.py
```

Must be run from the project root — imports are root-relative.

## Running Tests

There is no test framework. Test files are standalone scripts run directly:

```bash
python -m game_data.combat.patch_notes_test    # tests all negative-stat formulas
python -m game_data.combat.combat_example       # interactive combat walkthrough
```

## Architecture

### Data Flow

```
main.py
  └── game/pyrpg.py (PYRPG class)
        ├── game_data/data_inputs/input_name/input_name.py  (player creation / load)
        ├── game_data/combat/combat.py (Combat class, start_combat())
        └── game_data/data_actions/saves/player_data_save.py
```

### Path Registry Pattern

All CSV file paths are registered in `game_data/xml_db/data.xml`. Code never hard-codes paths — it calls `common_ops.get_data("node_name")` which resolves the path from the XML. Adding a new data file requires adding its path to `data.xml` first.

```python
# common_ops/common_ops.py
def get_data(node_name):   # parses data.xml, returns absolute path
def read_csv(file_name):   # returns list of rows (list of lists)
def check_existing_player(player_name):  # checks players_data/players.csv
```

### Dual Player Data Format

Player data exists in two shapes throughout the code — both must be handled with `isinstance` checks:
- **New player** (tuple): `(name, role, level, hp, stats_dict)` — returned by `NewPlayer.player_data()`
- **Existing player** (dict): `{"name", "role", "level", "stats"}` — returned by `check_existing_player()`

`PYRPG`, `Player` (combat), and `_do_save()` all contain explicit `isinstance(player_data, tuple)` branches for this reason.

### Combat System

`game_data/combat/combat.py` — `Combat` class manages one encounter. `start_combat(player_data, enemy_name)` is the public entry point.

`game_data/combat/damage_calculator.py` — `DamageCalculator` contains all stat-based formulas as static methods. Every formula maps directly to the Alpha II patch notes spec in `patch_notes/Alpha II.md`.

`game_data/combat/combat_player.py` — `Player` wraps player data for live HP tracking during combat. Stats and max HP are snapshotted at combat start and restored after (combat mutations don't persist).

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

- Roles: `game_data/stats/roles_x_stats/classes.csv` — columns: `Class, Strength, Agility, Intelligence, Defence, Magic, Luck`
- Enemies: `game_data/stats/enemies_x_stats/enemies.csv` — columns: `Name, HP, Attack, Defense, Speed, Luck`
- Save data: `players_data/players.csv` (gitignored)

Stats are read via `RolesExtract` and `get_enemy_stats()` which use `get_data()` + `read_csv()`.

### HP Formula

Player HP = `abs((Strength + Defence) / 0.2)` — used in both `NewPlayer` and `Player.calculate_hp()`.

### Known Broken Code

`enums/roles_enums/roles.py` and `enums/combat_enums/combat_enums.py` have import errors and reference non-existent methods. These files are not used by the active game flow and can be ignored or deleted.
