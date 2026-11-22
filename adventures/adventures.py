import random
from enemies.enemies_data import get_encounter_enemy, get_enemy_stats, DEATH


def parse_spawn(cell):
    """'Bear *2' -> ('Bear', 2), 'Mimic' -> ('Mimic', 1), '?x2' -> ('?x2', 1), '' -> None"""
    if not cell or not cell.strip():
        return None
    name, _, count = cell.partition("*")
    return name.strip(), int(count) if count.strip() else 1


def spawn_name(name):
    """The enemy's name as enemies.csv spells it ('slime' -> 'Slime')"""
    stats = get_enemy_stats(name)
    return stats["Name"] if stats else name


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


def graveyard(game, row):
    """Look around or walk on. Looking around always wakes the dead (the row's Enemy_spawn); put
    them back down and one of the graves turns out to be a chest. Returns the fight's result or None."""
    print("\nYou come across an old graveyard. Some of the graves look... freshly dug.")
    if input("Look around the graves? (y/n) ").strip().lower() != "y":
        print("You keep walking. Probably for the best.")
        return None

    spawn = parse_spawn(row.get("Enemy_spawn", ""))
    if not spawn:
        print("\nNothing stirs. In an open grave, a chest sits half-buried.")
        game.open_chest()
        return "chest"
    name, size = spawn_name(spawn[0]), spawn[1]
    print(f"\nThe ground shifts... {size} {name}s claw their way up!" if size > 1
          else f"\nThe ground shifts... a {name} claws its way up!")

    def grave_chest():
        print("In the grave they crawled out of, a chest sits half-buried.")
        game.open_chest()

    return game.fight(name, size, on_victory=grave_chest)


def sudden_hunger(game, row):
    """Only at half HP or less (the row's HP_req). You're so hungry that the snack is the row's
    Enemy_spawn (a Slime): take a bite and heal the row's Value... and it fights back.
    Returns the fight's result, or None."""
    heal = int(float((row.get("Value") or "0").lstrip("+=")))
    spawn = parse_spawn(row.get("Enemy_spawn", ""))
    name, size = (spawn_name(spawn[0]), spawn[1]) if spawn else (None, 0)
    if name:
        print(f"\nYour stomach growls. A {name} wobbles by, all glistening and jiggly. "
              f"It looks... kind of delicious?")
        prompt = f"Take a bite out of the {name}? (y/n) "
    else:
        print("\nYour stomach growls. On a rock nearby sits something that looks... edible. Mostly.")
        prompt = "Eat it? (y/n) "
    if input(prompt).strip().lower() != "y":
        print("You're not that hungry. Yet.")
        return None

    pd = game.player_data
    healed = max(0, min(heal, pd.max_hp - pd.hp))
    pd.hp += healed
    if not name:
        print(f"Not bad! You recover {healed} HP. HP: {pd.hp}/{pd.max_hp}")
        input("\nPress Enter to continue...")
        return "ate"
    print(f"*CHOMP* Tastes like... lime? You recover {healed} HP. HP: {pd.hp}/{pd.max_hp}")
    print(f"\nThe {name} did NOT enjoy that. It fights back!" if size == 1
          else f"\nTurns out it wasn't alone. {size} angry {name}s fight back!")
    return game.fight(name, size)


def halt(game, row):
    """Town event, -Charisma only: a guard stops you on the way back in. Pay a fine (15 ~ 40 gold,
    the closer to 0 your Charisma the cheaper) or refuse and fight. Lose and the guard takes the
    full top fine anyway, or everything you've got. Returns "paid" or the fight's result."""
    from adventures.encounters import parse_range, swayed
    low, high = parse_range(row.get("Cost"))
    fine = round(swayed(row, low, high, game, ugly_only=True))
    top_fine = round(high)
    pd = game.player_data

    print("\n\"Halt!\" A town guard steps into your path. \"You've been causing trouble, haven't you?\"")
    print(f"\"Pay a fine of {fine} gold, or we do this the hard way.\"")
    print(f"Gold: {pd.gold}")
    choice = input(f"[1] Pay the fine ({fine} gold)  [2] Refuse and fight: ").strip()
    if choice == "1":
        if pd.gold >= fine:
            pd.gold -= fine
            print("You pay up. \"Stay out of trouble.\" The guard steps aside.")
            input("\nPress Enter to continue...")
            return "paid"
        print("\"You don't even have that?\" The guard draws a sword.")
    else:
        print("\"The hard way it is.\"")

    spawn = parse_spawn(row.get("Enemy_spawn", "")) or ("Guard", 1)
    result = game.fight(spawn_name(spawn[0]), spawn[1])
    if result == "defeat":
        taken = min(pd.gold, top_fine)
        pd.gold -= taken
        print(f"While you're out cold, the guard helps themself to {taken} gold.")
        input("\nPress Enter to continue...")
    return result


# Encounter Description -> the function that runs it
ADVENTURES = {"Cave entrance": cave_entrance, "A strange obelisk": strange_obelisk,
              "Graveyard": graveyard, "Sudden Hunger": sudden_hunger, "Halt!": halt}
