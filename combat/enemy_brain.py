"""v1.1: enemies with brains. Decides what an enemy does on its turn; Combat carries it out.

Actions: "attack", "charge" (bide: the charged hit lands two turns later), "defend", "heal" (group
support only), "flee" (45% HP or less, wild fights only), and while charging, "release".

Solo enemies go by their own HP:
    phase 1 (80%+)     attack 60 / charge 20 / defend 20
    phase 2 (45-80%)   attack 50 / charge 10 / defend 40
    phase 3 (<=45%)    try to flee first, then attack 30 / charge 10 / defend 60
A charge goes: bide -> one more move (CHARGING_ODDS: attack or defend) -> the charged hit. A
charging enemy never flees, so biding means it's staying.

Groups: a hurt member (below 80%) acts like a solo enemy of its phase. Healthy members:
    everyone healthy   the leader (healthiest) uses phase 1, the others SUPPORT_ODDS[1]
    someone's hurt     SUPPORT_ODDS[2], which can heal: the least-HP member 65%, the leader 35%
                       (never itself, never a -Attack member — they heal themselves by leeching)

Its own random generator, so the dice the game rolls for damage never shift because of a decision
(and tests can script BRAIN).
"""
import random

from combat.damage_calculator import DamageCalculator

BRAIN = random.Random()

PHASE_2_AT = 0.80   # below this share of max HP: phase 2
PHASE_3_AT = 0.45   # at or below: phase 3

SOLO_ODDS = {
    1: {"attack": 60, "charge": 20, "defend": 20},
    2: {"attack": 50, "charge": 10, "defend": 40},
    3: {"attack": 30, "charge": 10, "defend": 60},
}
CHARGING_ODDS = {  # the move between biding and the charged hit
    1: {"attack": 65, "defend": 35},
    2: {"attack": 55, "defend": 45},
    3: {"attack": 33, "defend": 67},
}
SUPPORT_ODDS = {
    1: {"attack": 60, "charge": 30, "defend": 10},
    2: {"attack": 45, "charge": 15, "defend": 20, "heal": 20},
}
HEAL_LEAST_HP = 65  # % a healer goes for the most hurt member (else the leader)

# Enemy.charge: CHARGE_BIDING right after it bides, CHARGE_READY once its in-between move is done
CHARGE_BIDING = 2
CHARGE_READY = 1


def hp_share(enemy):
    return enemy.hp / enemy.max_hp if enemy.max_hp else 0


def phase(enemy):
    share = hp_share(enemy)
    if share >= PHASE_2_AT:
        return 1
    return 2 if share > PHASE_3_AT else 3


def pick(odds):
    actions = list(odds)
    return BRAIN.choices(actions, weights=[odds[a] for a in actions], k=1)[0]


def leader(alive):
    """The healthiest member (first one on a tie)"""
    return max(alive, key=hp_share)


def heal_target(healer, alive):
    """Who a support member would heal: hurt, not itself, not -Attack. 65% the least-HP one, 35%
    the leader (if the leader can't be healed, the least-HP one). None if nobody qualifies."""
    hurt = [e for e in alive if e is not healer and e.hp < e.max_hp and e.stats.get("Attack", 0) >= 0]
    if not hurt:
        return None
    weakest = min(hurt, key=hp_share)
    boss = leader(alive)
    if BRAIN.uniform(0, 100) >= HEAL_LEAST_HP and boss in hurt:
        return boss
    return weakest


def wants_to_flee(enemy):
    chance = DamageCalculator.enemy_flee_chance(enemy.stats.get("Speed", 0), enemy.stats.get("Luck", 0))
    return chance > 0 and BRAIN.uniform(0, 100) < chance


def decide(enemy, enemies, can_flee=True):
    """What `enemy` does this turn"""
    if enemy.charge == CHARGE_READY:
        return "release"
    if enemy.charge == CHARGE_BIDING:
        return pick(CHARGING_ODDS[phase(enemy)])

    own = phase(enemy)
    if own == 3 and can_flee and wants_to_flee(enemy):
        return "flee"

    alive = [e for e in enemies if e.is_alive()]
    if len(alive) <= 1 or own >= 2:
        return pick(SOLO_ODDS[own])

    if all(phase(e) == 1 for e in alive):
        return pick(SOLO_ODDS[1]) if leader(alive) is enemy else pick(SUPPORT_ODDS[1])

    action = pick(SUPPORT_ODDS[2])
    if action == "heal" and heal_target(enemy, alive) is None:
        return "attack"
    return action
