import random


def parse_spawn(cell):
    """'Bear *2' -> ('Bear', 2), 'Mimic' -> ('Mimic', 1), '' -> None"""
    if not cell or not cell.strip():
        return None
    name, _, count = cell.partition("*")
    return name.strip(), int(count) if count.strip() else 1


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

def strange_obelisk(game, row):
    """A strange obelisk. The player can choose to touch it or not. Touching it gives a random effect."""
    print("\nYou come across a strange obelisk. It hums with energy.")
    if input("Touch the obelisk? (y/n) ").strip().lower() != "y":
        print("You keep walking. Probably for the best.")
        return None

    # Random effect: either gain EXP, lose HP, or get a random item
    effects = ["gain_exp", "lose_hp", "random_item"]
    effect = random.choice(effects)

    if effect == "gain_exp":
        exp_gain = 100
        game.player.gain_exp(exp_gain)
        print(f"You feel a surge of knowledge! You gain {exp_gain} EXP.")
        return "gain_exp"

    elif effect == "lose_hp":
        hp_loss = 20
        game.player.take_damage(hp_loss)
        print(f"A sharp pain courses through your body! You lose {hp_loss} HP.")
        return "lose_hp"

    elif effect == "random_item":
        item = game.get_random_item()
        game.player.add_item(item)
        print(f"A mysterious item appears in your hands: {item.name}.")
        return "random_item"


# Encounter Description -> the function that runs it
ADVENTURES = {"Cave entrance": cave_entrance,"A strange obelisk": strange_obelisk,}
