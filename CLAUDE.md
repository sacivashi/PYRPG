# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Running the Game

```bash
python main.py
```

Must be run from the project root — imports are root-relative.

## Running Tests

```bash
pytest
```

`tests/` holds the automated suite (197 tests as of this writing). `conftest.py` at the project root is intentionally empty — its presence just tells pytest to add the project root to `sys.path` so test files can use the same root-relative imports as the game itself. There's also a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs on push to `master`/`beta-1` and on PRs: it import-checks `game.pyrpg`, `combat.combat`, and `combat.damage_calculator`, then installs `requirements-dev.txt` and runs `pytest -v`. Beyond the automated suite, testing is still manual too (`python main.py` and play through it).

## Working with Patch Notes

Files under `patch_notes/` (including drafts like `version 1.0.md`) are the user's own — don't proactively rewrite or add to them. Do write directly into them when asked, including phrasing like "help me write this up" or "add to the md" — that counts as being asked, not as overstepping.

When the conversation's intent is discussing/brainstorming a patch (ideas, direction, future plans — not just when a patch_notes file happens to be open), default to engaging with the ideas rather than validating them: skip formula tables, min/max correctness checks, and bug callouts unless asked directly. Switch back to normal rigor once the user says they're actually building/implementing something.

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

Player data flows as the `PlayerData` dataclass (`players/player_data.py`: `name, role, level, hp, stats, mana, max_hp, gold, loot, equipped, exp, in_town, distance, depth_reached, failed_attempts, quest_flags, completed_quests, known_spells, item_state, perks`) everywhere in the active game flow — both `NewPlayer.player_data()` and `get_player()` return one. `gold` (int, default 0) and `loot` (list of owned item names, default empty) are awarded outside of combat, in `pyrpg.py`, after a "victory" result — `Combat`/`Player` don't compute rewards themselves. `combat_player.py`'s `Player.__init__` also accepts a raw `(name, role, level, hp, stats)` tuple for backward compatibility (converted to a `PlayerData` and handled by the same branch), but nothing in the current flow produces one anymore.

`mana` is current mana (`None` = full, for new characters and pre-mana saves); max mana is never stored — always derived from gear-adjusted stats (`Player.calculate_mana()`: `max(20, abs(Intelligence) * 4.5)`). `depth_reached` is the deepest `distance` ever reached — only `explore()` raises it, nothing lowers it — and is fast travel's ceiling. `known_spells` holds learned spell/ability names (`spells/spells_data.py`); `item_state` holds per-item progress (Thunder item use counts, Sleight of stats wins/gains).

Every field added to `PlayerData` after the original set needs the same three-way wiring or it silently resets on save: `Player.__init__` (both the `PlayerData` branch and the bare-name fallback) and `Player.player_data()` to carry it through combat, `players/save.py` to write it, `util/file_io.py`'s `get_player()` to read it back (with a default, for saves predating the field). This bit gold/loot once early on — see git history — and every field since has followed the same pattern.

### Quests

Quests live in `data/quests.csv` — columns: `id, title, type, target, amount, reward, description` — read by `get_quests()` (`quests/quests_data.py`, same `get_data()` + `read_csv()` pattern; quote descriptions that contain commas). `_update_quest_progress(enemy_name, defeated)`, called after every combat victory with the group size, adds to `PlayerData.quest_flags[quest_id]` (a count, capped at `amount`) for every unfinished `"defeat"` quest whose `target` matches. The Town menu's `quest_board()` shows `progress/amount`, offers to claim (award `reward` gold, add the id to `PlayerData.completed_quests`) once it's reached, and shows "Completed" thereafter — `completed_quests` is what prevents re-claiming. `"use"` quests count an action instead — the game calls `_record_quest_use(action)` where it happens (so far only `FAST_TRAVEL`, from `fast_travel()`). `reward` is either gold (a number) or a perk name from `PERKS`; claimed perks go into `PlayerData.perks` and whatever they affect removes them when used (`free_fast_travel` makes the next fast travel cost 0). Adding a defeat quest is a new CSV row, not new code; a new `type`, a new `use` target, or a new perk needs its own hook. Saves from before the CSV stored a finished Lost Cat as `{"defeated_cat": True}` — `quest_progress()` still reads any `defeated_<target>: True` as complete.

### Equipment

`data/items.csv` — columns: `Name, Consumable, Strength, Agility, Intelligence, Defence, Magic, Luck, Rarity, Buyable, Droppable`, where each stat is a *delta* (can be negative) applied on top of the player's base stats, not an absolute value. Read via `get_item_stats()`/`get_item_names()` (`items/items_data.py`), same `get_data()` + `read_csv()` pattern as roles/enemies.

`PlayerData.equipped` holds at most one item name (single-slot, no weapon/armor split yet) or `None`. `Player` keeps two stat dicts: `base_stats` (pure copy of `player_data.stats`, what actually gets saved — never mutated by gear) and `stats` (the equipped-adjusted copy used for HP and all combat calculations, built by `Player.apply_equipment(base_stats, equipped_name)`). This split matters because gear can push a stat across zero in either direction — the existing negative-stat combat formulas already handle that fine (same as the curse mechanic crossing a stat through 0), so equipment needed no new combat logic, just the stat-layering.

Rarity is both the drop weight (higher = more common) and the price: `get_item_price()` = `max(15, int(abs(65 - rarity) * 0.65))` — the pivot is a fixed 65, not the highest rarity in the file, so adding a very common item doesn't reprice the shop. Consumables (`Consumable = Yes`) can't be equipped; `manage_loot()` uses them instead (`use_item_outside_combat()`: potions and spell-learning items), and combat-only ones are refused there. Health/Mana potions sit outside the rotating shop stock as always-stocked slots (`PYRPG.ALWAYS_STOCKED`). Some items drop as a stack (`PYRPG.DROP_STACK_SIZES`, e.g. Nuts x4); loot stays a flat list either way, and menus group duplicates for display (`_stacked_loot()`).

Equipping/unequipping is a menu-only action (`PYRPG.manage_loot()`), not something that happens mid-combat. Since max HP derives from Strength+Defence, changing gear changes max HP (and Intelligence gear changes max mana) — `PYRPG._apply_equipment_hp_change()` recomputes both and clamps current HP/mana to the new caps with no free heal on the way up. Level-up points and Sleight of stats work the same way (`_sync_max_hp_after_growth()`: the cap moves, current only clamps). This is deliberately different from `Player._resolve_current_hp()`'s heal-the-gap behavior on load, which is only for HP formula changes between game versions.

### Combat System

`combat/combat.py` — `Combat` class manages one encounter. `start_combat(player_data, enemy_name, group_size)` is the public entry point; it returns `(result, hp, mana)` and writes `loot`/`item_state` back onto `player_data` (items used up in a fight stay used up). Enemies are built at the player's `distance`, which drives the depth 50+ stat buff. Group odds/sizes come from `roll_group_size(depth)` (`GROUP_TIERS`).

`combat/damage_calculator.py` — `DamageCalculator` contains all stat-based formulas as static methods, mapped to `patch_notes/version 1.0.md` (physical/magic split). Every player hit on an enemy goes through `Combat._hit_enemy(target, damage, type)`: corrupted enemies (corr > 0) ignore Defense entirely and only subtract corr (a hit that doesn't clear it heals them); everyone else applies `enemy_defence_adjustment()` for `"physical"` (attacks + abilities), `"spell"`, or `"item"` (unaffected).

`combat/combat_player.py` — `Player` wraps player data for live HP/mana tracking during combat. Stats and max HP are snapshotted at combat start and restored after (combat stat mutations — curses, Berserker armor — don't persist).

### Spells & Abilities

`spells/spells_data.py` — `SPELLS` defines every spell (`kind`: `"spell"`, `"cursed"` (-Magic only, costs HP), `"ability"`), plus `LEARNING_ITEMS` (consumable -> spell it teaches), `EQUIPMENT_SPELLS` (gear -> spell granted while worn, e.g. Beam staff -> Hyper beam), `STARTING_ITEMS` (role -> starting learning item, given in `NewPlayer`), and `LEVEL_UP_SPELLS` (role -> {level: spells}, learned by `PYRPG._learn_level_up_spells()` after each level-up and on load, skipping anything not learnable yet). Behaviour specific to one spell (Mana surge's per-cast scaling, Hyper beam's all-mana cost, Blade rush channelling, Nature's gift heal-over-time, Berserk scream's `Combat.berserk_bonus`) is keyed off those definitions in `Combat.cast()`. Spells can be `"aoe"` (Ice shower) or carry `splash_damage` (Lava bomb); single-target abilities take their damage from `DamageCalculator.ABILITY_FORMULAS` and their type from `damage_type` — `"searing"` (Backstab) skips both Defense and corruption in `_hit_enemy`. The old "Magic Attack" is gone — combat option 2 is Spells & Abilities, and with nothing learned it just says so without using the turn.

### Encounters & Depth

`enemies/enemies_data.py` — `get_encounter_enemy(player_power, depth)` weights enemies by threat vs a target of `player_power * encounter_target_ratio(depth)` (`DEPTH_TARGET_RATIOS`; with no depth, the flat 2.5). From depth 100, Death can claim the encounter first (`death_chance()`); Death is in `NEVER_RANDOM_ENEMIES`, so it's never in the weighted pool, always solo, and can't be fled. `apply_depth_buff()` adds `depth - 50` to every positive enemy stat past depth 50.

### Adventures (v1.1, in progress)

`data/encounters.csv` (`get_data("encounters_csv")`) lists passive encounters — `Type, Description, Depth, Effect, Value, Duration, Cost, Odds, Enemy_spawn` — but nothing rolls from it yet. `Adventure` and `Event` rows only trigger; the steps live in code, in `adventures/adventures.py`'s `ADVENTURES` (Description -> function taking `(game, row)`). `Enemy_spawn` is `Name *N` (`parse_spawn()`), or `?xN` for "roll an enemy against N times the usual target for this depth" (`roll_spawn()` -> `get_encounter_enemy(power * N, depth)`; the Strange obelisk uses `?x2`). Adventure fights go through `PYRPG.fight(enemy, size)` (split out of `enter_combat()`, so rewards/death penalties match a random fight), and chests through `PYRPG.open_chest()` (5 ~ 13 gold + a loot roll). `open_chest()` is always a real chest — Mimics are their own encounter row, decided before it's called — which is why adventure chests are always safe.

### Negative Stat System

The core mechanic. Any stat can be negative. Each negative stat gives a debuff + a compensating benefit:

| Stat | Debuff | Benefit |
|------|--------|---------|
| -Strength | Physical attacks/abilities sear you for `int(abs(str) + int(min(max_hp*0.08, abs(str))*0.5))`, hit or miss | Landing heals `min((abs(str)+missing_hp)*0.8, (damage_done+abs(str))*0.65)` |
| -Agility | Always acts last | `+min(15, max(5, abs(-agi)))%` dodge/counter rate |
| -Intelligence | `min(35, abs(int)+5)%` chance a spell/ability costs 1.5x mana (or all of it) | Spells deal `int(0.5*spell_damage) + int(min(abs(int)//3, abs(mag)*0.8))` bonus |
| -Defence | Takes extra `max(max_hp*0.05, abs(-def))` damage | Reflects part of each hit back |
| -Magic | 15% less EXP; normal spells weak (`max(0.1, 1+mag*0.1)`) | Cursed spells: cost `min(abs(mag), cost*0.88)` HP, scale with `abs(mag)`, `min(65, int(sqrt(abs(mag))*10))%` to debuff the target |
| -Luck | `min(35, abs(-lck))%` miss chance | Successful attacks are unavoidable |

+Defence is a flat `min(25, 2 + def*0.7)%` damage reduction (0 or less: none). Defending adds a flat `min(10, max(0, def*0.75))` block on top, to every enemy hit until the player's next turn (`Combat.defending`).

Physical attack damage (`DamageCalculator.calculate_base_damage`) = `int(sqrt(abs(Str) + abs(Agi) + abs(Lck) + abs(Def) + 15) * 2.2)` — every physical stat counts by its size (negative stats included), so roles land close together; there's no Strength multiplier or +Luck random bonus anymore.

Enemies have a parallel negative-stat system documented in `patch_notes/Alpha II.md` (Defense/-Defense and Corruption reworked in `version 1.0.md`). **Corruption** (`Enemy.corruption`, the live value, starting at the CSV stat): at the end of its turn the enemy takes `max(current_hp*0.04, corr, 3)` searing damage, then corr grows by 1; and corruption replaces Defense for it entirely (see `_hit_enemy` above).

### Role and Enemy Stats

- Roles: `data/roles.csv` — columns: `Class, Strength, Agility, Intelligence, Defence, Magic, Luck`
- Enemies: `data/enemies.csv` — columns: `Name, Corruption, HP, Attack, Defense, Speed, Luck`
- Save data: `data/players.json` (gitignored) — `{"players": [{"name", "role", "level", "hp", "max_hp", "mana", "stats", "gold", "loot", ...}, ...]}` (every `PlayerData` field). `max_hp` is optional for backward compatibility with older saves (`None` if absent); when present, it lets `Player` detect max_hp increases (formula tweaks, stat changes) on load and heal the character by the difference instead of leaving them stranded below the new cap. `gold`/`loot` are similarly optional, defaulting to `0`/`[]` for saves that predate them.

Roles/enemies stats are read via `RolesExtract` (`roles/roles_data.py`) and `get_enemy_stats()` (`enemies/enemies_data.py`), both built on `get_data()` + `read_csv()`. Player saves use `get_data()` + `read_json()`/`write_json()` instead (`util/file_io.py`).

### HP Formula

Player HP = `max(22, abs(Strength) * 0.95 + abs(Defence) * 2.3)` — `Player.calculate_hp()` in `combat/combat_player.py`, used for both new and loaded players.
