from util.file_io import get_data, read_csv
import random

# Encounter weighting. Each enemy has a "difficulty" (sum of its absolute stats — the same
# score EXP uses). It's compared to a target scaled from the player's power: enemies near the
# target are the most likely, tougher ones fall off fast (but never to zero, so a rare
# out-of-depth fight can still happen), and weaker ones fade more gently.
ENCOUNTER_TARGET_RATIO = 2.5   # target difficulty = player power * this
ENCOUNTER_SHARPNESS = 4        # how quickly odds drop for enemies tougher than the target
MIN_WEAK_WEIGHT = 0.2          # floor for enemies far below the target
MIN_ENCOUNTER_WEIGHT = 0.001   # floor for everything, so weights never all collapse to 0


def get_enemy_names():
    reader = read_csv(get_data("enemies_csv"))
    name = random.choice([row[0] for row in reader if row[0] != "Name"])
    return name


def _parse_enemy_row(headers, row):
    return {"Name": row[0],
            **{
                headers[i]: int(row[i].strip()) if row[i].strip().lstrip('-').isdigit() else row[i].strip()
                for i in range(1, len(headers))
            }}


def get_enemy_stats(name):
    reader = read_csv(get_data("enemies_csv"))
    headers = reader[0]  # First row is the header
    for row in reader[1:]:  # Skip the header
        if row[0].lower() == name.lower():
            return _parse_enemy_row(headers, row)
    return None


def get_enemy_difficulty(enemy_stats):
    """Sum of the enemy's absolute stats (Name excluded)."""
    return sum(abs(int(v)) for k, v in enemy_stats.items() if k != 'Name')


def get_encounter_weight(difficulty, player_power):
    """Relative chance of meeting an enemy of this difficulty, given the player's power."""
    target = max(1, player_power * ENCOUNTER_TARGET_RATIO)
    ratio = difficulty / target
    if ratio <= 1:
        weight = max(MIN_WEAK_WEIGHT, ratio)
    else:
        weight = 1 / (1 + ((ratio - 1) * ENCOUNTER_SHARPNESS) ** 2)
    return max(MIN_ENCOUNTER_WEIGHT, weight)


def get_encounter_weights(player_power):
    """[(name, weight), ...] for every enemy, reading the CSV once."""
    reader = read_csv(get_data("enemies_csv"))
    headers = reader[0]
    weights = []
    for row in reader[1:]:
        if not row:
            continue
        stats = _parse_enemy_row(headers, row)
        weights.append((stats["Name"], get_encounter_weight(get_enemy_difficulty(stats), player_power)))
    return weights


def get_encounter_enemy(player_power):
    """Pick a random enemy, weighted toward ones that suit the player's current power."""
    names, weights = zip(*get_encounter_weights(player_power))
    return random.choices(names, weights=weights, k=1)[0]
