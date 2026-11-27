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

`tests/` holds the automated suite (370 tests as of this writing). `conftest.py` at the project root holds one autouse fixture (it points `players_json`/`unlocks_json` at temp files and makes `"Tester"` the active player, so no test writes the real saves or unlock progress) — its presence also tells pytest to add the project root to `sys.path` so test files can use the same root-relative imports as the game itself. There's also a GitHub Actions workflow (`.github/workflows/ci.yml`) that runs on push to `master`/`beta-1` and on PRs: it import-checks `game.pyrpg`, `combat.combat`, and `combat.damage_calculator`, then installs `requirements-dev.txt` (which pulls in `requirements.txt`: Rich) and runs `pytest -v`. Beyond the automated suite, testing is still manual too (`python main.py` and play through it).

## Working with Patch Notes

Files under `patch_notes/` (including drafts like `version 1.0.0.md`) are the user's own — don't proactively rewrite or add to them. Do write directly into them when asked, including phrasing like "help me write this up" or "add to the md" — that counts as being asked, not as overstepping.

When the conversation's intent is discussing/brainstorming a patch (ideas, direction, future plans — not just when a patch_notes file happens to be open), default to engaging with the ideas rather than validating them: skip formula tables, min/max correctness checks, and bug callouts unless asked directly. Switch back to normal rigor once the user says they're actually building/implementing something.

## Architecture

### Data Flow

```
main.py
  └── game/pyrpg.py (PYRPG class)
        ├── players/input_name.py (InputName.input_name() — title screen, player + adventurer choice)
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
def read_csv(file_name):   # csv.DictReader rows: one dict per row, keyed by header (row["Defense"]) — never index columns by position
def read_json(file_name) / write_json(file_name, data)  # player save data
def get_player(player_name, player=None):  # one of the active player's adventurers as PlayerData, or None
def get_adventurers(player=None):  # every adventurer a player owns
def delete_player(player_name):  # removes a player entry, returns True/False
```

### Player Data

Player data flows as the `PlayerData` dataclass (`players/player_data.py`: `name, role, level, hp, stats, mana, max_hp, gold, loot, equipped, exp, in_town, distance, depth_reached, failed_attempts, quest_flags, completed_quests, known_spells, item_state, perks, effects`) everywhere in the active game flow — both `NewPlayer.player_data()` and `get_player()` return one. `gold` (int, default 0) and `loot` (list of owned item names, default empty) are awarded outside of combat, in `pyrpg.py`, after a "victory" result — `Combat`/`Player` don't compute rewards themselves. `combat_player.py`'s `Player.__init__` also accepts a raw `(name, role, level, hp, stats)` tuple for backward compatibility (converted to a `PlayerData` and handled by the same branch), but nothing in the current flow produces one anymore.

`mana` is current mana (`None` = full, for new characters and pre-mana saves); max mana is never stored — always derived from gear-adjusted stats (`Player.calculate_mana()`: `max(20, abs(Intelligence) * 4.5)`). `depth_reached` is the deepest `distance` ever reached — only `explore()` raises it, nothing lowers it — and is fast travel's ceiling. `known_spells` holds learned spell/ability names (`spells/spells_data.py`); `item_state` holds per-item progress (Thunder item use counts, Sleight of stats wins/gains).

Adding a `PlayerData` field is one line in `player_data.py` (give it a default, for saves predating it) — nothing else copies fields by hand. `save.py` writes `asdict(player_data)`, `get_player()` reads every field the save has and lets the dataclass default the rest, and `Player` loops over `fields(PlayerData)` to carry everything through combat except `Player.DERIVED_FIELDS` (`hp`, `mana`, `max_hp`, `stats`, which it tracks as `current_hp`/`current_mana`/`max_hp`/`base_stats`). It used to be hand-wired in all three places, and missed fields silently reset on save; `tests/test_player_data_roundtrip.py` guards against that coming back. Load-time fixes for old saves (`_migrate_stats()`, `_rescue_item_rewards()`) live in `get_player()`.

### Quests

Quests live in `data/quests.csv` — columns: `id, title, type, target, amount, reward, charisma, choice, description, spawn` — read by `get_quests()` (`quests/quests_data.py`, same `get_data()` + `read_csv()` pattern; quote descriptions that contain commas). Each quest gets `options`, one per choice: `{label, cost, reward, charisma}`. Choice quests put one value per choice in `target` (spend only), `reward` and `charisma`, split by `/`, in the order of the `choice` labels (`55/0`, `Dice machine/0`, `+2/-2`, `Accept/Decline`); a single value applies to every choice, and no `choice` means one unlabelled option. Every quest is opt-in: only ids in `PlayerData.accepted_quests` count progress. Progress comes from one method, `PYRPG.quest_event(type, value, amount=1)`: the game reports what happened — `"defeat"` (enemy name, group size, after every victory), `"use"` (an action, so far only `FAST_TRAVEL` from `fast_travel()`), `"reach"` (the new distance, from `explore()` only, so fast travel doesn't count) — and it adds to `PlayerData.quest_flags[quest_id]` (a count, capped at `amount`) for every accepted, unfinished quest of that type whose `target` matches. How a type matches lives in `QUEST_TYPES` (`quests_data.py`; name equality, or `value >= target` for reach). The Town menu's `quest_board()` is a numbered list (`_quest_status()`: New / In progress / Ready to claim / Completed); opening one (`_open_quest()`) accepts it or leaves it for later ("not now"), shows progress, or claims it (`_complete_quest()`: pick an option, pay its `cost`, `grant_reward()`, add its `charisma` to `stats["Charisma"]`, record the label in `PlayerData.quest_choices`, then the id goes into `completed_quests`, which is what prevents re-claiming). Every choice completes the quest, refusing included. `"spend"` is the one non-event type: it skips accepting, and its choice is made (and paid) the moment you open it. `spawn` (`Townfolk *3`) is a fight that starts on accepting, in town, through `PYRPG.fight()`; until it's won the quest page offers the fight again. Quest-only enemies belong in `NEVER_RANDOM_ENEMIES`. `reward` is gold (a number; 0 = no reward, `describe_reward()` returns None), an item name from items.csv (goes into loot), or a perk name from `PERKS`; claimed perks go into `PlayerData.perks` and whatever they affect removes them when used (`free_fast_travel` makes the next fast travel cost 0). Quest chains come from `data/unlocks.csv` (`get_data("unlocks_csv")`): a row with `unlocks = quest:<id>` and `type = quest` hides that quest until the quest in its `target` is completed (`quest_unlocked()`); the other unlocks.csv rows are global unlocks (see Unlocks & Flavor below). Adding a quest of an existing type is a new CSV row, not new code; a new `type` is one `QUEST_TYPES` line plus a `quest_event()` call where it happens, and a new perk needs a hook wherever it takes effect. Old saves: `get_player()` fills `accepted_quests` with every quest they had finished or made progress on (`started_quests()`), and a finished Lost Cat saved as `{"defeated_cat": True}` from before the CSV still reads as complete (`quest_progress()`).

### Charisma

`stats["Charisma"]` (`util/charisma.py`, `CHARISMA`) sways people, never fights: combat only reads stats by name, `_player_power()` leaves it out of encounter matching, and it isn't in `STAT_COLUMNS`, so level-up points and Sleight of stats can't raise it (gear can: items use `ITEM_STAT_COLUMNS`). It changes through quests and gear only. Shop prices go through `charisma_price(base, cha)`: `int(min(15, abs(cha) * 0.48))`% cheaper for +Charisma, pricier for -Charisma, then the Voucher on top (`PYRPG._shop_price()`). Saves from before Charisma get their class's value from roles.csv (`_migrate_stats()`).

### Equipment

`data/items.csv` — columns: `Name, Consumable, Strength, Agility, Intelligence, Defense, Magic, Luck, Rarity, Buyable, Droppable`, where each stat is a *delta* (can be negative) applied on top of the player's base stats, not an absolute value. Read via `get_item_stats()`/`get_item_names()` (`items/items_data.py`), same `get_data()` + `read_csv()` pattern as roles/enemies.

`PlayerData.equipped` holds at most one item name (single-slot, no weapon/armor split yet) or `None`. `Player` keeps two stat dicts: `base_stats` (pure copy of `player_data.stats`, what actually gets saved — never mutated by gear) and `stats` (the equipped-adjusted copy used for HP and all combat calculations, built by `Player.apply_equipment(base_stats, equipped_name)`). This split matters because gear can push a stat across zero in either direction — the existing negative-stat combat formulas already handle that fine (same as the curse mechanic crossing a stat through 0), so equipment needed no new combat logic, just the stat-layering.

Rarity is both the drop weight (higher = more common) and the price: `get_item_price()` = `max(15, int(abs(65 - rarity) * 0.65))` — the pivot is a fixed 65, not the highest rarity in the file, so adding a very common item doesn't reprice the shop. Consumables (`Consumable = Yes`) can't be equipped; `manage_loot()` uses them instead (`use_item_outside_combat()`: potions and spell-learning items), and combat-only ones are refused there. Shop and merchant stock are picked by `rarity_sample()` (weighted by Rarity, like drops). Health/Mana potions sit outside the rotating shop stock as always-stocked slots (`PYRPG.ALWAYS_STOCKED`). Some items drop as a stack (`PYRPG.DROP_STACK_SIZES`, e.g. Nuts x4); loot stays a flat list either way, and menus group duplicates for display (`_stacked_loot()`).

Equipping/unequipping is a menu-only action (`PYRPG.manage_loot()`), not something that happens mid-combat. Since max HP derives from Strength+Defense, changing gear changes max HP (and Intelligence gear changes max mana) — `PYRPG._apply_equipment_hp_change()` recomputes both and clamps current HP/mana to the new caps with no free heal on the way up. Level-up points and Sleight of stats work the same way (`_sync_max_hp_after_growth()`: the cap moves, current only clamps). This is deliberately different from `Player._resolve_current_hp()`'s heal-the-gap behavior on load, which is only for HP formula changes between game versions.

### Combat System

`combat/combat.py` — `Combat` class manages one encounter. `start_combat(player_data, enemy_name, group_size)` is the public entry point; it returns `(result, hp, mana)` and writes `loot`/`item_state` back onto `player_data` (items used up in a fight stay used up). Enemies are built at the player's `distance`, which drives the depth 50+ stat buff. Group odds/sizes come from `roll_group_size(depth)` (`GROUP_TIERS`).

`combat/damage_calculator.py` — `DamageCalculator` contains all stat-based formulas as static methods, mapped to `patch_notes/version 1.0.0.md` (physical/magic split). Every player hit on an enemy goes through `Combat._hit_enemy(target, damage, type)`: corrupted enemies (corr > 0) ignore Defense entirely and only subtract corr (a hit that doesn't clear it heals them); everyone else applies `enemy_defence_adjustment()` for `"physical"` (attacks + abilities), `"spell"`, or `"item"` (unaffected).

`combat/enemy_brain.py` (v1.1) decides each enemy turn — `decide(enemy, enemies, can_flee)` returns `attack`/`charge`/`defend`/`heal`/`flee`/`release` from HP phases (`phase()`: 80%+ / 45-80% / <=45%) and the `SOLO_ODDS`/`CHARGING_ODDS`/`SUPPORT_ODDS` tables (groups: the healthiest is the `leader()`, hurt members act solo, healthy ones support; `heal_target()`). It has its own `BRAIN` random generator, so decisions never shift the damage dice and tests can script it. `Combat.enemy_turn()` carries the action out: a charge bides (`Enemy.charge` = `CHARGE_BIDING`), makes one in-between move, then lands (`_charged_attack()`: Attack x1.5, or a -Attack enemy's usual hit + 1.3x siphon searing); `Enemy.defending` adds `enemy_defend_block()` to physical hits in `_hit_enemy` and a 15% `_maybe_counter()`; `_enemy_flees()` sets `Enemy.fled` (`is_alive()` is False, but it isn't defeated) and may drop gold/loot (`flee_gold`/`flee_loot`, paid unless you lose). Special fights never flee: `start_combat(..., special=True)` and `NEVER_RANDOM_ENEMIES`; `PYRPG.fight()` defaults to `special=True`, and only `enter_combat()` passes `special=False` (Death excepted). `start_combat()` returns a `FightResult` — still unpacks as `(result, hp, mana)`, plus `.fled`; a fight where every enemy ran off is `"enemy_fled"` (no rewards, no `victory` event, so nothing ticks), and `fight()` pays gold/EXP/loot only for the enemies actually beaten. The numbers live in `DamageCalculator` (`CHARGE_MULTIPLIER`, `ENEMY_COUNTER_CHANCE`, `enemy_flee_chance()`, `enemy_heal_chance()`...).

`combat/combat_player.py` — `Player` wraps player data for live HP/mana tracking during combat. Stats and max HP are snapshotted at combat start and restored after (combat stat mutations — curses, Berserker armor — don't persist).

### Spells & Abilities

`spells/spells_data.py` — `SPELLS` defines every spell (`kind`: `"spell"`, `"cursed"` (-Magic only, costs HP), `"ability"`), plus `LEARNING_ITEMS` (consumable -> spell it teaches), `EQUIPMENT_SPELLS` (gear -> spell granted while worn, e.g. Beam staff -> Hyper beam), `STARTING_ITEMS` (role -> starting learning item, given in `NewPlayer`), and `LEVEL_UP_SPELLS` (role -> {level: spells}, learned by `PYRPG._learn_level_up_spells()` after each level-up and on load, skipping anything not learnable yet). Behaviour specific to one spell (Mana surge's per-cast scaling, Hyper beam's all-mana cost, Blade rush channelling, Nature's gift heal-over-time, Berserk scream's `Combat.berserk_bonus`) is keyed off those definitions in `Combat.cast()`. Spells can be `"aoe"` (Ice shower) or carry `splash_damage` (Lava bomb); single-target abilities take their damage from `DamageCalculator.ABILITY_FORMULAS` and their type from `damage_type` — `"searing"` (Backstab) skips both Defense and corruption in `_hit_enemy`. Use limits come from `uses_per_combat()` (`once_per_combat`, or `uses_per_combat: N`); limited abilities can cost 0 mana (Pirate: Rum x2 from level 1 heals and drops Intelligence for the fight, `_drink_rum()`; Flintlock x1 from level 3, whose coin proc (`_flintlock_coins()`) builds `Combat.bonus_gold`, paid by `start_combat()` on a win only). Cut (a buyable learning item) is a 2-mana searing chip. The old "Magic Attack" is gone — combat option 2 is Spells & Abilities, and with nothing learned it just says so without using the turn.

### Encounters & Depth

`enemies/enemies_data.py` — `get_encounter_enemy(player_power, depth)` weights enemies by threat vs a target of `player_power * encounter_target_ratio(depth)` (`DEPTH_TARGET_RATIOS`; with no depth, the flat 2.5). From depth 100, Death can claim the encounter first (`death_chance()`); Death is in `NEVER_RANDOM_ENEMIES`, so it's never in the weighted pool, always solo, and can't be fled. `apply_depth_buff()` adds `depth - 50` to every positive enemy stat past depth 50.

### Encounters & Adventures (v1.0.6, being built)

`data/encounters.csv` (`get_data("encounters_csv")`) lists passive encounters — `Type, Description, Depth, Effect, Value, Duration, Cost, Odds, Enemy_spawn, Charisma_effect, Charisma_req, HP_req`. `adventures/encounters.py` rolls them: `explore()` calls `PYRPG.passive_encounter()` first (25%, `roll_wild_encounter()`) and only fights if nothing came up; a successful `return_to_town()` calls `town_encounter()` (`roll_town_encounter()`, already back in town). A row is eligible (`eligible()`) if its `Depth` fits (a number = that depth or deeper, `town` = town only), `Charisma_req`/`HP_req` pass (`meets()`: `<0`, `<=50%` of max HP...) and it has a handler — rows of a type with no handler yet are simply never rolled. Wild `Odds` are weights; town `Odds` are a straight % each. Bad rows (`is_bad()`: `Curse`, or a `Chest`/`Merchant` with an `Enemy_spawn`, i.e. a Mimic or thief merchant in disguise) get their weight swayed by Charisma (`odds_sway_percent()`, up to 20% either way). Disguised ones can be seen through with Intelligence (`first_impression()`, `notice_chance()`). `Charisma_effect = yes` prices slide along their `low~high` range (`swayed()` -> `charisma_range()`; Halt! uses `ugly_only`).

Handlers: `ENCOUNTER_TYPES` (Type -> function, `encounters.py`: `Chest`, `Healer`, `Merchant`, `Boon`/`Curse` -> `sculpture()`) and `ADVENTURES` (Description -> function, `adventures/adventures.py`, for `Adventure`/`Event` rows), each taking `(game, row)`. `Enemy_spawn` is `Name *N` (`parse_spawn()`, `spawn_name()` fixes the case), or `?xN` for "roll an enemy against N times the usual target for this depth" (`roll_spawn()`; the Strange obelisk uses `?x2`). Encounter fights go through `PYRPG.fight(enemy, size, surprise=, scaling=, on_victory=)` so rewards/death penalties match a random fight: `surprise` puts every enemy first in the turn order, `scaling` adds a flat bonus to the enemy's positive stats (Mimics: `depth - 1`, plus the 50+ buff), `on_victory` is an extra payout after the usual rewards. Chests go through `PYRPG.open_chest()` (5 ~ 13 gold + a loot roll), which is always a real chest — Mimics are their own row, decided before it's called — so adventure chests are always safe. Mimic and Guard are in `NEVER_RANDOM_ENEMIES`. Merchants (`merchant()`) sell `merchant_stock()` (`MERCHANT_SHOP_ITEMS` shop items + `MERCHANT_EXCLUSIVES` (a min~max range) exclusives the shop never sells, i.e. droppable-but-not-buyable) at the row's `Cost` markup (`*=1.3`, Charisma only if `Charisma_effect = yes`) and buy loot at `SELL_RATE` (35% of `base_price()`, which uses the always-stocked price for potions). A thief merchant is the same row with `Enemy_spawn = Thief`: the first trade hands over the gold/item and starts a surprise fight scaled like a Mimic, and winning gives back what was handed over (`_thief_strikes()`).

### Boons, Curses & Events

Prayer sculptures (`Boon`/`Curse` rows, `sculpture()`) and the Prayer card (`prayer_card()`) start a temporary effect (`util/effects.py`, `make_effect(row)`: `Effect` = a stat or one of `BONUS_TICKS`' targets `rest_chance`, `rest_restoration`, `gold`, `EXP`, `max_hp`; `Value` = `+=`/`-=`/`*=`; `Duration` = how many of its events before it wears off, blank = until a successful rest or a town rest). They live in `PlayerData.effects`, the one field with `metadata={"saved": False}`: `save.py`/`get_player()` only touch `saved_fields()`, so a curse can never be saved. Stats layer as base -> gear (`_gear_stats()`) -> effects (`_effective_stats()`, `apply_effects()`); combat's `Player` does the same, and max HP is `Player.max_hp_with_effects()` (Of growth) everywhere. `_player_power()` uses `_gear_stats()`, so curses don't make encounters easier. A boon/curse starting or ending moves the HP cap like a gear change (`_refresh_max_hp()`).

`util/events.py`'s `EventBus` is the game's event listener: `PYRPG.events` (built on first use, since tests skip `__init__`) gets `explore`, `rest`, `rested`, `town_rest`, `victory` (enemy, size), `fast_travel` (depth), `defeated` (enemy) and `prayed` (a sculpture, answered or not). Quests listen to it (`victory` -> `quest_event("defeat")`, `explore` -> `"reach"`, `fast_travel` -> `"use"`, `prayed` -> `"use", "sculpture"` for Test of Faith), unlocks count on it, and effects tick on it (`_tick_effects()`). New reactions should be listeners, not calls added where things happen.

### Players & Adventurers (v1.1.1)

A **player** (the person, `players/profiles.py`) owns **adventurers** (characters, `PlayerData`) and their own unlock progress. `data/players.json` is `{"Players": {"<player>": {"Adventurers": [{...every saved PlayerData field...}], "Unlocks": {"progress": {}, "unlocked": []}}}}`. Player and adventurer names aren't case sensitive (found in any case, shown as first written); adventurer names only clash within one player. `profiles.ACTIVE` is who's playing, set by the start menu: `get_player()`/`put_new_player()`/`delete_player()` and unlocks all go to them. The start flow (`players/input_name.py`): the banner, then `[1] New Player` (a player name, straight into their first adventurer), `[2] My Adventurers` (player name, then a table of their adventurers to load/delete, or create one; an unknown name offers to make that player), `[3] Exit`. Empty answers go back a step; deleting needs the adventurer's name typed out. New adventurers are saved at once and saving is always on. Saves from before players (`{"players": [...]}`) are never read: `archive_old_saves()` renames them to `players_old.json` (and the old shared `unlocks.json` to `unlocks_old.json`) at startup, numbering the name if a backup already exists.

### Unlocks & Flavor (v1.0.7)

`unlocks/unlocks.py` reads `data/unlocks.csv` (`id, unlocks, type, target, amount, role, hint`; `quest:` rows are per-character quest chains, skipped here). `unlocks` is `class:` / `enemy:` / `item:` / `event:` + a name; several rows can unlock the same thing (any one is enough); `role` limits a row to one class. Anything no row unlocks is never locked. Progress belongs to the **player** (v1.1.1; shared by everyone before) and lives in their `Unlocks` entry in `data/players.json` (`profiles.load_unlocks()`/`save_unlocks()`), next to their adventurers; with no active player it's kept in memory only. Two kinds of row (the module docstring lists every type): counters, fed by `record(type, value, amount, role)` — `defeat`/`defeated`/`use` from the event bus, `charisma_quest` from `_complete_quest()`, and `encounter`/`block`/`attack_heal`/`mana_spent`/`zeroed` from `start_combat()` (`Combat.tally`); and thresholds (`equip`, `stat_below`/`stat_above` on gear stats, `max_hp`, `quest`), checked by `check_state()` via `PYRPG._check_unlocks()` at every menu and after claiming a quest. Locks are applied where things are picked: `get_encounter_weights()` (enemies), `get_droppable_items()`/`get_buyable_items()` (items), `encounters.eligible()` (`event:<Description>`, e.g. Halt!), and `InputRole.choose_role()` (classes, shown as `???` with hint and progress). Enemy/event unlocks are announced quietly (`QUIET`). `grant(key)` unlocks something outright. The Journal (town menu [8]) prints `journal_lines()` plus the character's quest choices.

`util/flavor.py`: `FLAVOR` maps a moment to `(chance %, lines)`; `say(moment, enemy=, name=, item=, gold=)` rolls and prints one. It has its own `random.Random`, so flavor never shifts the game's dice (tests that patch `random.*` are unaffected). Enemy-flee lines are held for 1.1 (enemies can't flee yet).

`util/display.py` (v1.1.1) is the whole terminal look: `bar`, `gauge`, `divider`, `options`, `menu`, `table`, `banner`, `paint`, `number` for rounding displayed damage. Color comes from Rich (`requirements.txt`) and is switched on once by `display.enable()` in `main.py`, only when Rich is installed and stdout is a real terminal; otherwise (tests, pipes, no Rich) every helper returns the same plain text as before, so tests never see escape codes. Once on, `sys.stdout` is wrapped so every printed line goes through `highlight()`: `HIGHLIGHTS` (regex -> Rich style) colors damage, HP, gold, EXP, headers, option keys and enemy tags without the printing code knowing — new message styles are a `HIGHLIGHTS` line, not color codes in game code. Combat's turn header (`Combat.print_status()`), its action grid (`Combat.ACTION_MENU`), the town/wild menus (`PYRPG.TOWN_MENU`/`WILD_MENU`) and View Stats go through it. Bars sit in a thin middle-gray frame (`FRAME`, `FRAME_STYLE`). The title screen's version is `version.py`'s `VERSION`. Auto-saves are quiet (`put_new_player(..., quiet=True)`, a single "(auto-saved)" line).

### Negative Stat System

The core mechanic. Any stat can be negative. Each negative stat gives a debuff + a compensating benefit:

| Stat | Debuff | Benefit |
|------|--------|---------|
| -Strength | Physical attacks/abilities sear you for `int(abs(str) + int(min(max_hp*0.08, abs(str))*0.5))`, hit or miss | Landing heals `min((abs(str)+missing_hp)*0.8, (damage_done+abs(str))*0.65)` |
| -Agility | Always acts last | `+min(15, max(5, abs(-agi)))%` dodge/counter rate |
| -Intelligence | `min(35, abs(int)+5)%` chance a spell/ability costs 1.5x mana (or all of it) | Spells deal `int(0.5*spell_damage) + int(min(abs(int)//3, abs(mag)*0.8))` bonus |
| -Defense | Takes extra `max(max_hp*0.05, abs(-def))` damage | Reflects part of each hit back |
| -Magic | 15% less EXP; normal spells weak (`max(0.1, 1+mag*0.1)`) | Cursed spells: cost `min(abs(mag), cost*0.88)` HP, scale with `abs(mag)`, `min(65, int(sqrt(abs(mag))*10))%` to debuff the target |
| -Luck | `min(35, abs(-lck))%` miss chance | Successful attacks are unavoidable |

+Defense is a flat `min(25, 2 + def*0.7)%` damage reduction (0 or less: none). Defending adds a flat `min(10, max(0, def*0.75))` block on top, to every enemy hit until the player's next turn (`Combat.defending`).

Physical attack damage (`DamageCalculator.calculate_base_damage`) = `int(sqrt(abs(Str) + abs(Agi) + abs(Lck) + abs(Def) + 15) * 2.2)` — every physical stat counts by its size (negative stats included), so roles land close together; there's no Strength multiplier or +Luck random bonus anymore.

Enemies have a parallel negative-stat system documented in `patch_notes/Alpha II.md` (Defense/-Defense and Corruption reworked in `version 1.0.0.md`). **Corruption** (`Enemy.corruption`, the live value, starting at the CSV stat): at the end of its turn the enemy takes `max(current_hp*0.04, corr, 3)` searing damage, then corr grows by 1; and corruption replaces Defense for it entirely (see `_hit_enemy` above).

### Role and Enemy Stats

- Roles: `data/roles.csv` — columns: `Class, Strength, Agility, Intelligence, Defense, Magic, Luck`
- Enemies: `data/enemies.csv` — columns: `Name, Corruption, HP, Attack, Defense, Speed, Luck`
- Save data: `data/players.json` (gitignored) — players, each with their adventurers (every saved `PlayerData` field) and unlocks; see Players & Adventurers above. `max_hp` is optional for backward compatibility with older saves (`None` if absent); when present, it lets `Player` detect max_hp increases (formula tweaks, stat changes) on load and heal the character by the difference instead of leaving them stranded below the new cap. `gold`/`loot` are similarly optional, defaulting to `0`/`[]` for saves that predate them.

Roles/enemies stats are read via `RolesExtract` (`roles/roles_data.py`) and `get_enemy_stats()` (`enemies/enemies_data.py`), both built on `get_data()` + `read_csv()`. Player saves use `get_data()` + `read_json()`/`write_json()` instead (`util/file_io.py`).

### HP Formula

Player HP = `max(22, abs(Strength) * 0.95 + abs(Defense) * 2.3)` — `Player.calculate_hp()` in `combat/combat_player.py`, used for both new and loaded players.
