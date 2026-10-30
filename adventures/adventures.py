import random
from enemies.enemies_data import get_encounter_enemy, DEATH


def parse_spawn(cell):
    """'Bear *2' -> ('Bear', 2), 'Mimic' -> ('Mimic', 1), '?x2' -> ('?x2', 1), '' -> None"""
    if not cell or not cell.strip():
        return None
    name, _, count = cell.partition("*")
    return name.strip(), int(count) if count.strip() else 1


def roll_spawn(game, cell):
    """Turn an Enemy_spawn cell into (enemy, size). A named enemy is used as-is; '?xN' rolls one
    the normal way, but against N times the usual target for this depth — N times stronger than
    what you'd normally meet here, wherever "here" is."""
    spawn = parse_spawn(cell)
    if spawn is None:
        return None
    name, size = spawn
    if name.startswith("?x"):
        name = get_encounter_enemy(game._player_power() * float(name[2:]), game.player_data.distance)
    return name, 1 if name == DEATH else size


# What's waiting inside — weights, same as encounter Odds
CAVE_OUTCOMES = {"bears": 60, "chest": 40}


def cave_entrance(game, row):
    """Enter or walk past. Inside it's either the Enemy_spawn group or a chest — and a chest found
    on an adventure is always a real one, never a Mimic. Returns the fight's result, "chest", or
    None if the player walked on."""
    print("\nYou come across a dark cave entrance. You can't see what's inside.")
    if input("Enter the cave? (y/n) ").strip().lower() != "y":
        print("You keep walking. Probably for the best.")
        return None

    outcome = random.choices(list(CAVE_OUTCOMES), weights=list(CAVE_OUTCOMES.values()))[0]
    spawn = parse_spawn(row.get("Enemy_spawn", ""))

    if outcome == "bears" and spawn:       # a cave row with no Enemy_spawn only ever holds chests
        enemy, size = spawn
        print(f"\n{size} {enemy}s wake up, and they're not happy!" if size > 1
              else f"\nA {enemy} wakes up, and it's not happy!")
        return game.fight(enemy, size)

    print("\nThe cave is quiet. In the back, a chest sits against the wall.")
    game.open_chest()
    return "chest"


OBELISK_OUTCOMES = {"exp": 50, "enemy": 50}
OBELISK_EXP = 100                          # % EXP — always exactly one level


def strange_obelisk(game, row):
    """Touch it or walk on. Touching it either grants a full level's worth of EXP or wakes up
    something far stronger than usual (the row's Enemy_spawn, e.g. '?x2'). Returns "exp", the
    fight's result, or None if the player walked on."""
    print("\nYou come across a strange obelisk. It hums with energy.")
    if input("Touch the obelisk? (y/n) ").strip().lower() != "y":
        print("You keep walking. Probably for the best.")
        return None

    outcome = random.choices(list(OBELISK_OUTCOMES), weights=list(OBELISK_OUTCOMES.values()))[0]
    spawn = roll_spawn(game, row.get("Enemy_spawn", "")) if outcome == "enemy" else None

    if spawn:                              # an obelisk row with no Enemy_spawn only ever grants EXP
        enemy, size = spawn
        print(f"\nThe obelisk goes dark... and {size} {enemy}s step out of its shadow!" if size > 1
              else f"\nThe obelisk goes dark... and a {enemy} steps out of its shadow!")
        return game.fight(enemy, size)

    game.player_data.exp += OBELISK_EXP
    print(f"\nKnowledge floods your mind! You gain {OBELISK_EXP}% EXP.")
    game._process_level_ups()
    return "exp"


# Encounter Description -> the function that runs it
ADVENTURES = {"Cave entrance": cave_entrance, "A strange obelisk": strange_obelisk}
