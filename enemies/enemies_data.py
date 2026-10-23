from util.file_io import get_data, read_csv
import random

# Encounter weighting. Each enemy has a "threat" score — HP and Attack in full, other stats
# scaled down, so a fast/lucky-but-fragile enemy (e.g. Goblin: 60 Speed, 50 Luck, only 10 HP)
# doesn't read as more dangerous than its HP/Attack actually make it. This is deliberately
# separate from get_enemy_difficulty(), which EXP uses and counts every stat equally.
# Threat is compared to a target scaled from the player's power: enemies near the target are
# the most likely, tougher ones fall off fast (but never to zero, so a rare out-of-depth fight
# can still happen), and weaker ones fade more gently.
THREAT_WEIGHTS = {'HP': 1.0, 'Attack': 1.0, 'Defense': 0.5, 'Speed': 0.3, 'Luck': 0.3, 'Corruption': 0.5}
ENCOUNTER_TARGET_RATIO = 2.5   # target threat = player power * this (no depth given)
ENCOUNTER_SHARPNESS = 4        # how quickly odds drop for enemies tougher than the target
MIN_WEAK_WEIGHT = 0.2          # floor for enemies far below the target
MIN_ENCOUNTER_WEIGHT = 0.001   # floor for everything, so weights never all collapse to 0

# v1.0: depth shifts the target too — shallow trips lean easy, deep ones lean hard.
# (deepest depth in the tier, target ratio); the last tier covers everything deeper.
DEPTH_TARGET_RATIOS = [
    (5, 1.5),     # 1-5: easier for you to defeat
    (10, 2.25),   # 6-10: a mix of easy and somewhat tougher
    (15, 3.0),    # 11-15: tougher to medium
    (20, 4.0),    # 16-20: medium to hard
    (None, 5.0),  # 21+: hard to insane
]

DEATH = "Death"
DEATH_START_DEPTH = 100        # min(100, depth - 99)% chance any encounter at 100+ is Death
NEVER_RANDOM_ENEMIES = {"death"}  # only ever met through the depth roll, never the weighted pool
DEPTH_BUFF_START = 50          # past this, every positive enemy stat gets +(depth - 50)


def encounter_target_ratio(depth):
    for deepest, ratio in DEPTH_TARGET_RATIOS:
        if deepest is None or depth <= deepest:
            return ratio


def death_chance(depth):
    """% chance an encounter is Death: min(100, depth - 99) from depth 100 on"""
    return min(100, depth - (DEATH_START_DEPTH - 1)) if depth >= DEATH_START_DEPTH else 0


def apply_depth_buff(enemy_stats, depth):
    """Past depth 50, every stat above 0 grows by depth - 50. Negative and zero stats are left
    alone, so negative-stat mechanics and corruption-free enemies stay as designed."""
    if depth <= DEPTH_BUFF_START or enemy_stats["Name"].lower() in NEVER_RANDOM_ENEMIES:
        return enemy_stats
    bonus = depth - DEPTH_BUFF_START
    return {k: (v + bonus if k != "Name" and isinstance(v, int) and v > 0 else v) for k, v in enemy_stats.items()}


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
    """Sum of the enemy's absolute stats (Name excluded). Drives EXP — every stat counts equally."""
    return sum(abs(int(v)) for k, v in enemy_stats.items() if k != 'Name')


def get_enemy_threat(enemy_stats):
    """Weighted danger score (see THREAT_WEIGHTS above). Drives encounter matching only."""
    return sum(abs(int(v)) * THREAT_WEIGHTS.get(k, 1.0) for k, v in enemy_stats.items() if k != 'Name')


def get_encounter_weight(threat, player_power, target_ratio=ENCOUNTER_TARGET_RATIO):
    """Relative chance of meeting an enemy of this threat level, given the player's power."""
    target = max(1, player_power * target_ratio)
    ratio = threat / target
    if ratio <= 1:
        weight = max(MIN_WEAK_WEIGHT, ratio)
    else:
        weight = 1 / (1 + ((ratio - 1) * ENCOUNTER_SHARPNESS) ** 2)
    return max(MIN_ENCOUNTER_WEIGHT, weight)


def get_encounter_weights(player_power, depth=None):
    """[(name, weight), ...] for every randomly-encounterable enemy, reading the CSV once.
    With a depth, the target ratio comes from DEPTH_TARGET_RATIOS instead of the flat default."""
    target_ratio = ENCOUNTER_TARGET_RATIO if depth is None else encounter_target_ratio(depth)
    reader = read_csv(get_data("enemies_csv"))
    headers = reader[0]
    weights = []
    for row in reader[1:]:
        if not row or row[0].lower() in NEVER_RANDOM_ENEMIES:
            continue
        stats = _parse_enemy_row(headers, row)
        weights.append((stats["Name"], get_encounter_weight(get_enemy_threat(stats), player_power, target_ratio)))
    return weights


def get_encounter_enemy(player_power, depth=None):
    """Pick a random enemy, weighted toward ones that suit the player's power (and depth, if given).
    From depth 100 on, Death can claim the encounter before the weighted pick happens."""
    if depth is not None and random.randint(1, 100) <= death_chance(depth):
        return DEATH
    names, weights = zip(*get_encounter_weights(player_power, depth))
    return random.choices(names, weights=weights, k=1)[0]
