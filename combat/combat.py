import random
from combat.damage_calculator import DamageCalculator
from combat.combat_player import Player
from enemies.enemies_data import get_enemy_stats, apply_depth_buff, DEATH, DEPTH_BUFF_START, NEVER_RANDOM_ENEMIES
from combat import enemy_brain
from combat.enemy_brain import BRAIN, CHARGE_BIDING, CHARGE_READY
from util.flavor import line as flavor_line, say, fled_line
from util.display import divider, framed, number, options
from spells.spells_data import uses_per_combat, get_spell, spell_cost, spell_base_damage, blade_rush_damage, equipment_spell

# Group encounters — v1.0: the odds and sizes both scale with depth.
# (deepest depth in the tier, group chance %, {group size: weight})
GROUP_TIERS = [
    (5, 5, {2: 100}),
    (10, 8, {2: 100}),
    (15, 15, {2: 60, 3: 40}),
    (20, 25, {2: 55, 3: 45}),
]
DEEP_GROUP_SIZES = {2: 40, 3: 60}  # depth 21+
GROUP_SIZES = (2, 3)


def group_chance(depth):
    """% chance a fight is a group: tiered up to depth 20, then min(50, 35 + (depth - 21))"""
    for deepest, chance, _ in GROUP_TIERS:
        if depth <= deepest:
            return chance
    return min(50, 35 + (depth - 21))


def group_size_weights(depth):
    for deepest, _, sizes in GROUP_TIERS:
        if depth <= deepest:
            return sizes
    return DEEP_GROUP_SIZES


def roll_group_size(depth=0):
    """Solo (1) or a group of 2-3 of the same enemy, with depth-based odds"""
    if random.randint(1, 100) <= group_chance(depth):
        sizes = group_size_weights(depth)
        return random.choices(list(sizes), weights=list(sizes.values()), k=1)[0]
    return 1


class Enemy:
    """One member of a (possibly solo) enemy group. Each has its own HP, stats (so a debuff
    on one doesn't affect its siblings), corruption, and initiative/dodge_bonus."""

    def __init__(self, name, depth=0, scaling=0):
        self.name = name
        self.stats = self._scaled_stats(name, depth, scaling)
        self.max_hp = self._calculate_hp()
        self.hp = self.max_hp
        self.corruption = self.stats.get('Corruption', 0)  # live value — grows by 1 each of its turns
        self.dodge_bonus = 0
        self.initiative = 0
        self.defending = False  # v1.1: guarding until its next turn
        self.charge = 0         # v1.1: CHARGE_BIDING / CHARGE_READY while a charged attack winds up
        self.fled = False       # v1.1: ran off — gone from the fight, but not defeated

    @staticmethod
    def _scaled_stats(name, depth, scaling):
        """The CSV stats with the depth 50+ buff. `scaling` is a flat bonus to every stat above 0 on
        top of that, for enemies that grow with depth themselves (Mimics, thief merchants: depth - 1).
        Those get the 50+ buff too, even when they're never in the random pool."""
        stats = get_enemy_stats(name)
        if not scaling:
            return apply_depth_buff(stats, depth)
        bonus = scaling + max(0, depth - DEPTH_BUFF_START)
        return {k: (v + bonus if k != "Name" and isinstance(v, int) and v > 0 else v) for k, v in stats.items()}

    def _calculate_hp(self):
        if 'HP' in self.stats:
            return self.stats['HP']
        # Fallback calculation if no HP stat
        strength = self.stats.get('Strength', 5)
        defence = self.stats.get('Defense', 5)
        return abs((strength + defence) * 2)

    def is_alive(self):
        """Still in the fight: has HP left and hasn't fled"""
        return self.hp > 0 and not self.fled


class FightResult(tuple):
    """(result, hp, mana), like before, plus `fled`: how many enemies ran off. Unpacks as 3."""

    def __new__(cls, result, hp, mana, fled=0):
        obj = super().__new__(cls, (result, hp, mana))
        obj.fled = fled
        return obj


class Combat:
    MANA_REGEN_PERCENT = 0.10  # of max mana, at the start of every player turn after the first
    TIMER_COOLDOWN = 6         # player turns after the Timer's bonus turn before it can be used again
    POTION_AMOUNT = 20         # Health potion HP / Mana potion mana
    BOMB_DAMAGE = 35
    DICE_MACHINE_USES = 6      # per combat
    THUNDER_EVOLVE_USES = 6    # lifetime uses before a Thunder item upgrades
    # Thunder item -> (AOE damage, what it becomes after THUNDER_EVOLVE_USES uses)
    THUNDER_ITEMS = {
        "thunder apprentice": (6, "Thunder disciple"),
        "thunder disciple": (12, "Thunder master"),
        "thunder master": (18, None),
    }
    NUTS_HEAL = 5
    COMBAT_USABLE_ITEMS = ["bomb", "timer", "health potion", "mana potion", "nuts", "dice machine", *THUNDER_ITEMS]
    BERSERKER_ARMOR = "berserker armor"

    def __init__(self, player_data, enemy_name, group_size=1, surprise=False, scaling=0, special=False):
        self.player = Player(player_data)
        # v1.1: special encounters (Mimics, Death, Guards, thieves, quest and adventure fights) use the
        # same brains but never flee
        self.enemies_can_flee = not special and enemy_name.lower() not in NEVER_RANDOM_ENEMIES
        self.fled_count = 0
        self.flee_gold = 0      # dropped by enemies that fled, paid out unless you lose
        self.flee_loot = []
        depth = player_data.distance
        self.enemies = [Enemy(enemy_name, depth, scaling) for _ in range(group_size)]
        self.surprise = surprise  # a surprise attack: every enemy acts before the player

        # Calculate initiative for turn order — player and every enemy get their own
        self.player_initiative, self.player_dodge_bonus = self.calculate_initiative(self.player.get_live_stats()['stats'])
        for enemy in self.enemies:
            enemy.initiative, enemy.dodge_bonus = self.calculate_initiative(enemy.stats)

        # Turn order is a queue built once from everyone's initiative, cycled by advance_turn()
        self.turn_order = self._build_turn_order()
        self.turn_pointer = 0
        self.current_turn, self.current_enemy_index = self.turn_order[0]

        self.combat_ongoing = True
        self.allow_saves = False  # Block saves during combat
        self.timer_cooldown = 0  # Turns remaining before Timer can be used again
        self.bonus_turn = False  # True while taking the Timer's extra turn — it doesn't tick the cooldown
        self.player_turns_taken = 0  # first turn gets no mana regen — nothing has been spent yet
        self.player_fled = False
        self.cannot_flee = enemy_name.lower() == DEATH.lower()
        self.spell_casts = {}  # spell name -> casts this combat (Mana surge scaling, Hyper beam once)
        self.items_used = {}  # lowercased item name -> uses this combat (Thunder once, Dice machine 6x)
        self.channel = None  # {"name": ..., "turns_left": n} while a channelled ability (Blade rush) runs
        self.heal_over_time_turns = 0  # Nature's gift ticks remaining
        self.berserk_bonus = 0  # Berserk scream's flat physical damage bonus, once screamed
        self.bonus_gold = 0  # coins knocked loose mid-fight (Flintlock), paid out on a win
        self.defending = False  # set by Defend, lasts until the player's next turn
        # What this fight counts toward unlocks (unlocks/unlocks.py), reported by start_combat()
        self.tally = {"block": 0, "attack_heal": 0, "mana_spent": 0, "zeroed": 0}
        # Snapshots — both restored after combat ends
        self.original_player_stats = dict(self.player.stats)
        self.original_player_max_hp = self.player.max_hp

        foes = self.enemies[0].name if group_size == 1 else f"{group_size} {self.enemies[0].name}s"
        print(f"\n=== Combat: {foes} ===")
        if self.surprise:
            print("It's a surprise attack! They strike first!")
        elif self.current_turn == "player":
            print("You're quicker, you go first!")
        else:
            print(f"The {self._current_enemy().name} is quicker, it goes first!")

    def _current_enemy(self):
        return self.enemies[self.current_enemy_index]

    def _build_turn_order(self):
        """[(kind, enemy_index), ...] sorted by initiative, highest first. kind is 'player' or 'enemy'."""
        order = [("player", None, self.player_initiative)]
        for i, enemy in enumerate(self.enemies):
            order.append(("enemy", i, enemy.initiative))
        order.sort(key=lambda entry: (entry[0] == "enemy" and self.surprise, entry[2]), reverse=True)
        return [(kind, idx) for kind, idx, _ in order]

    def calculate_initiative(self, stats):
        """Calculate turn order based on Agility/Speed using patch notes specs"""
        agility = stats.get('Agility', stats.get('Speed', 0))
        initiative, dodge_counter_bonus = DamageCalculator.apply_agility_modifier(agility)

        # Store dodge/counter bonus for negative agility characters
        if agility < 0:
            return initiative, dodge_counter_bonus
        else:
            return initiative + random.randint(0, 5), 0

    def advance_turn(self):
        """Move to the next combatant in turn order, skipping any dead enemies."""
        for _ in range(len(self.turn_order)):
            self.turn_pointer = (self.turn_pointer + 1) % len(self.turn_order)
            kind, idx = self.turn_order[self.turn_pointer]
            if kind == "player" or self.enemies[idx].is_alive():
                self.current_turn, self.current_enemy_index = kind, idx
                return

    def _live_stats(self):
        return self.player.get_live_stats()['stats']

    def _check_victory(self):
        if not any(e.is_alive() for e in self.enemies):
            self.combat_ongoing = False

    def _check_player_defeated(self):
        if not self.player.is_alive():
            print("You have been defeated!")
            self.combat_ongoing = False
            return True
        return False

    # --- Player turn ----------------------------------------------------------------------------

    def player_turn(self):
        """Handle player's turn with menu options"""
        self.defending = False  # a Defend from last turn ends now
        if self.bonus_turn:
            self.bonus_turn = False
        elif self.timer_cooldown > 0:
            self.timer_cooldown -= 1
        if self.player_turns_taken > 0:
            self.regenerate_mana()
        self.player_turns_taken += 1

        self._berserker_check()
        self._tick_heal_over_time()

        self.print_status()

        if self.channel:
            # Channelling (Blade rush) takes the whole turn — no other actions until it ends
            self._continue_channel()
            self.advance_turn()
            return

        while True:
            print()
            print(self.ACTION_MENU)
            choice = input("> ").strip()

            # No save option during combat!
            if choice in ["save", "s"]:
                print("❌ Cannot save during combat!")
                continue

            if choice == "1":
                if not self.player_attack():
                    print("Turn ends.")
                self.advance_turn()
                break
            elif choice == "2":
                if self.cast_menu() is None:
                    continue  # nothing learned, cancelled, or couldn't afford it — doesn't use the turn
                self.advance_turn()
                break
            elif choice == "3":
                self.player_defend()
                self.advance_turn()
                break
            elif choice == "4":
                print("You skip your turn.")
                self.advance_turn()
                break
            elif choice == "5":
                outcome = self.use_item()
                if outcome is None:
                    continue  # cancelled or invalid — doesn't consume the turn
                if outcome == "end_turn":
                    self.advance_turn()
                else:
                    self.bonus_turn = True  # "repeat_turn" (Timer): stay on player's turn, no advance_turn()
                break
            elif choice == "6":
                if self.cannot_flee:
                    if not say("flee_death"):
                        print("You cannot flee.")
                    continue
                if not self.attempt_flee():
                    self.advance_turn()  # failed flee costs the turn, same as a missed attack
                break  # successful flee: combat_ongoing is now False, no turn to advance to
            else:
                print("Pick an action from 1 to 6.")

    def regenerate_mana(self):
        """Natural per-turn regen: MANA_REGEN_PERCENT of max mana, capped at max"""
        regen = int(self.player.max_mana * self.MANA_REGEN_PERCENT)
        self.player.current_mana = min(self.player.max_mana, self.player.current_mana + regen)

    def _berserker_check(self):
        """Berserker armor: every turn spent at or below half HP grants +1 Strength until combat ends"""
        if (self.player.equipped or "").lower() != self.BERSERKER_ARMOR:
            return
        if self.player.current_hp <= self.player.max_hp / 2:
            self.player.stats['Strength'] = self.player.stats.get('Strength', 0) + 1
            print(f"Berserker rage! Strength rises to {self.player.stats['Strength']}.")

    def _tick_heal_over_time(self):
        if self.heal_over_time_turns <= 0:
            return
        amount = get_spell("Nature's gift")["heal_per_turn"]
        self.player.heal(amount)
        self.heal_over_time_turns -= 1
        print(f"Nature's gift heals you for {amount} HP. ({self.player.current_hp}/{self.player.max_hp})")

    def _choose_target(self):
        """Auto-picks the lone survivor; prompts when more than one enemy is still alive."""
        alive = [i for i, e in enumerate(self.enemies) if e.is_alive()]
        if not alive:
            return None
        if len(alive) == 1:
            return alive[0]

        print("\nWho do you target?")
        for i in alive:
            e = self.enemies[i]
            print(f"  [{i + 1}] {self._label(i)} ({round(e.hp)}/{round(e.max_hp)} HP)")

        while True:
            choice = input("> ").strip()
            try:
                index = int(choice) - 1
            except ValueError:
                index = -1
            if index in alive:
                return index
            print("Invalid choice.")

    ACTION_MENU = options([("1", "Attack"), ("2", "Spells & Abilities"), ("3", "Defend"),
                           ("4", "Skip"), ("5", "Item"), ("6", "Flee")])

    def _label(self, index):
        """'Wolf', or 'Wolf #2' in a group"""
        enemy = self.enemies[index]
        return enemy.name if len(self.enemies) == 1 else f"{enemy.name} #{index + 1}"

    def print_status(self):
        """The turn header: a divider, then you and every enemy with HP (and your mana) bars"""
        names = [self.player.name] + [self._label(i) for i in range(len(self.enemies))]
        width = max(len(name) for name in names) + 3
        print(f"\n{divider(f'Turn {self.player_turns_taken}')}")
        print(framed([(f"  {self.player.name:<{width}}", "HP", self.player.current_hp, self.player.max_hp),
                      (f"  {'':<{width}}", "MP", self.player.current_mana, self.player.max_mana)]))
        print()  # a gap between you and the enemies
        for i, enemy in enumerate(self.enemies):
            if enemy.is_alive():
                tags = [tag for tag, on in (("charging!", enemy.charge), ("guarding", enemy.defending)) if on]
                status = f"  ({', '.join(tags)})" if tags else ""
                print(framed([(f"  {self._label(i):<{width}}", "HP", enemy.hp, enemy.max_hp, status)]))
            else:
                print(f"  {self._label(i):<{width}}{'(fled)' if enemy.fled else '(defeated)'}")

    def attempt_flee(self):
        """Attempt to flee: chance depends on the player's Agility and the enemy's Speed
        (DamageCalculator.calculate_flee_chance — group members share the same base stats,
        so any one of them gives the right Speed). Success ends combat immediately, no
        rewards and no penalty. Failure just costs the turn, like a missed attack."""
        agility = self._live_stats().get('Agility', 0)
        enemy_speed = self.enemies[0].stats.get('Speed', 0)
        flee_chance = DamageCalculator.calculate_flee_chance(agility, enemy_speed)

        roll = random.randint(1, 100)
        print(f"\nYou attempt to flee... ({flee_chance:g}% chance of success)")

        if roll <= flee_chance:
            print("You successfully flee from combat!")
            say("flee", name=self.player.name, enemy=self.enemies[0].name)
            self.player_fled = True
            self.combat_ongoing = False
            return True

        print("You fail to escape!")
        say("flee_fail", name=self.player.name, enemy=self.enemies[0].name)
        return False

    # --- Damage the player deals ------------------------------------------------------------------

    def _hit_enemy(self, target, damage, damage_type):
        """Land damage on an enemy and return how much it actually took. Corrupted enemies ignore
        their Defense entirely — corruption is their only protection, and a hit that doesn't clear
        it heals them. Everyone else goes through Defense (physical/spell/item, see
        DamageCalculator.enemy_defence_adjustment), and -Defense can reflect physical hits.
        Searing damage (Backstab) can't be blocked or reduced at all — not by Defense, not by corruption."""
        from_full = target.hp >= target.max_hp
        if damage_type == "searing":
            target.hp = max(0, round(target.hp - damage))
            print(f"You deal {round(damage)} searing damage to the {target.name}!")
            dealt = damage
        elif target.corruption > 0:
            dealt, heal = DamageCalculator.corruption_hit(damage, target.corruption)
            if heal > 0:
                target.hp = min(target.max_hp, round(target.hp + heal))
                print(f"Corruption swallows the hit and heals the {target.name} for {number(heal)} HP!")
            else:
                target.hp = max(0, round(target.hp - dealt))
                print(f"You deal {round(dealt)} searing damage to the {target.name}!")
        else:
            dealt, reflected = DamageCalculator.enemy_defence_adjustment(damage, target.stats.get('Defense', 0), damage_type)
            if damage_type == "physical" and target.defending:
                block = DamageCalculator.enemy_defend_block(target.stats.get('Defense', 0))
                if block:
                    dealt = max(0, dealt - block)
                    print(f"The {target.name}'s guard blocks {block} damage!")
            target.hp = max(0, round(target.hp - dealt))
            print(f"You deal {round(dealt)} damage to the {target.name}!")
            if reflected > 0:
                self.player.take_damage(reflected)
                print(f"You take {number(reflected)} reflected damage!")
                self._check_player_defeated()

        if target.hp <= 0:
            # a one-hit kill's flavor line says it better, so it takes the defeat line's place
            comment = flavor_line("one_hit", enemy=target.name) if from_full else None
            print(f"  » {comment}" if comment else f"The {target.name} is defeated!")
            self._check_victory()
        elif damage_type == "physical" and target.defending and self.player.is_alive():
            self._maybe_counter(target)
        return dealt

    def _maybe_counter(self, enemy):
        """v1.1: a defending enemy hit physically strikes back 15% of the time — its usual hit (a -Attack
        enemy's leeching one) plus a bit of its Defense. It's a normal hit: Defense, dodge and Defend apply."""
        if BRAIN.uniform(0, 100) >= DamageCalculator.ENEMY_COUNTER_CHANCE:
            return
        print(f"The {enemy.name} counters from behind its guard!")
        self.enemy_attack(enemy, bonus=DamageCalculator.enemy_counter_bonus(enemy.stats.get('Defense', 0)))

    def _apply_strength_curse(self, landed, damage_done):
        """-Strength after a physical attack or damaging ability: searing self-damage hit or miss,
        then — only if it landed and you're still standing — the heal"""
        strength = self._live_stats().get('Strength', 0)
        if strength >= 0:
            return
        self_damage = DamageCalculator.strength_self_damage(strength, self.player.max_hp)
        self.player.take_damage(self_damage)
        print(f"Your cursed strength sears you for {self_damage} HP!")
        if self._check_player_defeated():
            return
        if landed:
            missing_hp = self.player.max_hp - self.player.current_hp
            heal = DamageCalculator.strength_heal(strength, missing_hp, damage_done)
            before = self.player.current_hp
            self.player.heal(heal)
            self.tally["attack_heal"] += self.player.current_hp - before
            print(f"You heal {heal} HP from the blow!")

    def player_attack(self):
        """Physical attack on a chosen enemy. Returns True if it landed."""
        target_index = self._choose_target()
        if target_index is None:
            return False
        target = self.enemies[target_index]
        say("attack")

        damage, unavoidable = DamageCalculator.calculate_player_damage(self._live_stats())
        landed = False
        dealt = 0

        if damage <= 0:
            print("Your attack completely misses!")
            say("missed", enemy=target.name)
        else:
            damage += self.berserk_bonus  # Berserk scream: flat bonus on physical attacks until combat ends
            dodged, countered = (False, False) if unavoidable else DamageCalculator.roll_dodge(target.dodge_bonus)
            if dodged:
                print(f"The {target.name} dodges your attack!")
                say("missed", enemy=target.name)
            else:
                landed = True
                dealt = self._hit_enemy(target, damage, "physical")
                if countered and self.player.is_alive():
                    counter_damage = random.randint(1, 5)
                    self.player.take_damage(counter_damage)
                    print(f"Enemy counters for {counter_damage} damage!")
                    self._check_player_defeated()

        if self.player.is_alive():
            self._apply_strength_curse(landed, dealt)
        return landed

    # --- Spells & abilities -------------------------------------------------------------------------

    def available_spells(self):
        """Learned spells/abilities you can use right now, plus any granted by gear. Cursed spells
        only show while Magic is negative — gear can push it either way."""
        magic = self._live_stats().get('Magic', 0)
        names = [name for name in self.player.known_spells
                 if get_spell(name) and (get_spell(name)["kind"] != "cursed" or magic < 0)]
        granted = equipment_spell(self.player.equipped)
        if granted and granted not in names:
            names.append(granted)
        return names

    def _cost_label(self, name):
        spell = get_spell(name)
        casts = self.spell_casts.get(name, 0)
        limit = uses_per_combat(name)
        if limit and casts >= limit:
            return "used up this fight"
        if spell["cost"] == "all":
            return "all your mana"
        if limit:
            return f"{limit - casts}/{limit} left this fight" + (f", {spell['cost']} mana" if spell["cost"] else "")
        cost = spell_cost(name, casts)
        if spell["kind"] == "cursed":
            hp_cost = DamageCalculator.cursed_hp_cost(self._live_stats().get('Magic', 0), cost)
            return f"{round(hp_cost, 1)} HP"
        return f"{cost} mana"

    def cast_menu(self):
        """Pick a spell or ability. Returns 'end_turn', or None if nothing was cast."""
        spells = self.available_spells()
        if not spells:
            print("You have no spells or abilities.")
            return None

        print("\nSpells & Abilities:")
        for i, name in enumerate(spells, 1):
            print(f"  [{i}] {name} ({get_spell(name)['kind']}, {self._cost_label(name)})")
        print("  [0] Back")

        choice = input("Choose: ").strip()
        if choice == "0":
            return None
        try:
            index = int(choice) - 1
            if index < 0 or index >= len(spells):
                raise ValueError
        except ValueError:
            print("Invalid choice.")
            return None
        return self.cast(spells[index])

    def _rolled_waste(self):
        chance = DamageCalculator.mana_waste_chance(self._live_stats().get('Intelligence', 0))
        return chance > 0 and random.randint(1, 100) <= chance

    def cast(self, name):
        """Pay for and resolve one spell/ability. Returns 'end_turn', or None if it couldn't be cast."""
        spell = get_spell(name)
        stats = self._live_stats()
        magic = stats.get('Magic', 0)
        intelligence = stats.get('Intelligence', 0)
        casts = self.spell_casts.get(name, 0)

        limit = uses_per_combat(name)
        if limit and casts >= limit:
            print(f"{name} can only be used {'once' if limit == 1 else f'{limit} times'} per fight.")
            return None

        cost = spell_cost(name, casts, self.player.current_mana)

        if spell["kind"] == "cursed":
            hp_cost = DamageCalculator.cursed_hp_cost(magic, cost)
            if self._rolled_waste():
                hp_cost *= 1.5
                print("Your muddled mind botches the ritual — it demands more blood!")
            hp_cost = round(hp_cost)
            self.player.take_damage(hp_cost)
            print(f"{name} costs you {hp_cost} HP.")
            if not self.player.is_alive():
                print("You couldn't pay the price... the curse consumes you.")
                self.combat_ongoing = False
                return "end_turn"
        else:
            if cost > self.player.current_mana:
                print(f"Not enough mana for {name} (needs {cost}, you have {self.player.current_mana}).")
                return None
            spent = cost
            if cost and self._rolled_waste():
                spent = min(self.player.current_mana, int(cost * 1.5))
                print(f"Your focus slips and you waste mana — {name} costs {spent}!")
            self.player.current_mana -= spent
            self.tally["mana_spent"] += spent

        self.spell_casts[name] = casts + 1
        print(f"You use {name}!")
        if spell["kind"] in ("spell", "cursed"):
            say("magic" if spell["kind"] == "spell" else "cursed_spell", item=name)

        if name == "Blade rush":
            self.channel = {"name": name, "turns_left": spell["channel_turns"]}
            self._continue_channel()
        elif name == "Nature's gift":
            self.heal_over_time_turns = spell["heal_turns"]
            self._tick_heal_over_time()
        elif name == "Berserk scream":
            self._berserk_scream()
        elif name == "Rum":
            self._drink_rum()
        elif spell["kind"] == "ability":
            self._cast_ability_hit(name, spell)
        else:
            self._cast_damage_spell(name, spell, casts, cost, magic, intelligence)
        return "end_turn"

    def _spell_hit_damage(self, base, magic, intelligence, cursed):
        damage = base * DamageCalculator.spell_multiplier(magic, cursed)
        return damage + DamageCalculator.intelligence_spell_bonus(damage, intelligence, magic)

    def _cast_damage_spell(self, name, spell, casts, mana_spent, magic, intelligence):
        """Spells and cursed spells: Magic-scaled damage (+ the -Int bonus) to one target, or to every
        enemy for "aoe" spells. A splash_damage spell then hits every living enemy, the target too."""
        cursed = spell["kind"] == "cursed"
        damage = self._spell_hit_damage(spell_base_damage(name, casts, mana_spent), magic, intelligence, cursed)

        if spell["target"] == "aoe":
            for enemy in self.enemies:
                if enemy.is_alive():
                    self._hit_enemy(enemy, damage, "spell")
            return

        target_index = self._choose_target()
        if target_index is None:
            return
        target = self.enemies[target_index]
        self._hit_enemy(target, damage, "spell")

        if spell.get("splash_damage"):
            splash = self._spell_hit_damage(spell["splash_damage"], magic, intelligence, cursed)
            print(f"The {name.lower()} explodes!")
            for enemy in self.enemies:
                if enemy.is_alive():
                    self._hit_enemy(enemy, splash, "spell")

        if cursed and target.is_alive() and random.randint(1, 100) <= DamageCalculator.cursed_debuff_chance(magic):
            self.apply_debuff_to_enemy(target, DamageCalculator.cursed_debuff_amount(magic))

    def _cast_ability_hit(self, name, spell):
        """Single-target damage abilities (Arrowshot, Backstab, Blade bonk, Shield bash): their own
        formula (DamageCalculator.ability_damage), no spell boosts, can't miss or be dodged. Being
        abilities, they still trigger the -Strength curse."""
        target_index = self._choose_target()
        if target_index is None:
            return
        damage = DamageCalculator.ability_damage(name, self._live_stats())
        if name == "Flintlock":
            print("*BANG* Pearly barks!")
        dealt = self._hit_enemy(self.enemies[target_index], damage, spell["damage_type"])
        if name == "Flintlock":
            self._flintlock_coins()
        if self.player.is_alive():
            self._apply_strength_curse(True, dealt)

    def _flintlock_coins(self):
        """A Flintlock hit may knock some coins loose: paid out with the rewards if you win"""
        luck = self._live_stats().get('Luck', 0)
        if random.uniform(0, 100) < DamageCalculator.flintlock_gold_chance(luck):
            gold = DamageCalculator.flintlock_gold(luck)
            self.bonus_gold += gold
            print(f"*clink* The shot knocks {gold} coins loose!")

    def _drink_rum(self):
        """Rum: heal, then lose Intelligence for the rest of the fight (reset by the stat snapshot)"""
        stats = self._live_stats()
        before = self.player.current_hp
        self.player.heal(DamageCalculator.rum_heal(stats))
        loss = DamageCalculator.rum_int_loss(stats.get('Intelligence', 0))
        self.player.stats['Intelligence'] = stats.get('Intelligence', 0) - loss
        print(f"*glug glug* You heal {self.player.current_hp - before} HP "
              f"({self.player.current_hp}/{self.player.max_hp}). *hic* "
              f"Intelligence drops to {self.player.stats['Intelligence']}.")

    def _berserk_scream(self):
        """Physical attacks deal +int(max(1, str * 0.45)) until combat ends; Intelligence drops by
        int(max_hp * 0.80), possibly below 0. Both reset when the fight ends (stat snapshot)."""
        stats = self._live_stats()
        self.berserk_bonus = DamageCalculator.berserk_bonus(stats.get('Strength', 0))
        int_loss = int(self.player.max_hp * 0.80)
        self.player.stats['Intelligence'] = stats.get('Intelligence', 0) - int_loss
        print(f"You let out a berserk scream! Physical attacks deal +{self.berserk_bonus} damage, "
              f"but your Intelligence drops to {self.player.stats['Intelligence']}.")

    def _continue_channel(self):
        """One turn of Blade rush: physical damage to every living enemy, then the -Strength curse"""
        damage = blade_rush_damage(self._live_stats())
        print(f"Blade rush! ({self.channel['turns_left']} turn(s) left)")
        dealt = sum(self._hit_enemy(e, damage, "physical") for e in self.enemies if e.is_alive())
        self.channel["turns_left"] -= 1
        if self.channel["turns_left"] <= 0:
            self.channel = None
            print("Your blade rush comes to an end.")
        if self.player.is_alive():
            self._apply_strength_curse(True, dealt)

    # --- Items ------------------------------------------------------------------------------------

    def use_item(self):
        """Use a combat item from loot. Returns 'end_turn', 'repeat_turn', or None (cancelled/invalid)."""
        available = []
        for item in self.player.loot:
            if item.lower() in self.COMBAT_USABLE_ITEMS and item not in available:
                available.append(item)
        if not available:
            print("You have no usable items.")
            return None

        print("\nUsable items:")
        for i, item in enumerate(available, 1):
            count = self.player.loot.count(item)
            suffix = f" x{count}" if count > 1 else ""
            if item.lower() == "timer" and self.timer_cooldown > 0:
                suffix += f" (cooldown: {self.timer_cooldown} more turns)"
            print(f"  [{i}] {item}{suffix}")
        print("  [0] Cancel")

        choice = input("Choose an item to use: ").strip()
        if choice == "0":
            return None

        try:
            index = int(choice) - 1
            if index < 0 or index >= len(available):
                raise ValueError
        except ValueError:
            print("Invalid choice.")
            return None

        item = available[index]
        key = item.lower()

        if key == "bomb":
            self.player.loot.remove(item)
            print("You throw a Bomb!")
            self._hit_all(self.BOMB_DAMAGE)
            return "end_turn"

        if key == "timer":
            if self.timer_cooldown > 0:
                print(f"Timer is on cooldown for {self.timer_cooldown} more turns.")
                return None
            print("Time freezes around you! You act again immediately.")
            self.timer_cooldown = self.TIMER_COOLDOWN
            return "repeat_turn"

        if key == "nuts":
            self.player.loot.remove(item)
            self.player.heal(self.NUTS_HEAL)
            print(f"You munch some Nuts. HP: {self.player.current_hp}/{self.player.max_hp}")
            return "end_turn"

        if key == "health potion":
            self.player.loot.remove(item)
            self.player.heal(self.POTION_AMOUNT)
            print(f"You drink a Health potion. HP: {self.player.current_hp}/{self.player.max_hp}")
            return "end_turn"

        if key == "mana potion":
            self.player.loot.remove(item)
            self.player.current_mana = min(self.player.max_mana, self.player.current_mana + self.POTION_AMOUNT)
            print(f"You drink a Mana potion. Mana: {self.player.current_mana}/{self.player.max_mana}")
            return "end_turn"

        if key == "dice machine":
            used = self.items_used.get(key, 0)
            if used >= self.DICE_MACHINE_USES:
                print(f"The Dice machine is out of rolls this fight ({self.DICE_MACHINE_USES} max).")
                return None
            self.items_used[key] = used + 1
            roll = random.randint(1, 6)
            print(f"The Dice machine rolls a {roll}! A huge dice slams down on the enemies!")
            self._hit_all(roll)
            return "end_turn"

        if key in self.THUNDER_ITEMS:
            if self.items_used.get(key):
                print(f"{item} can only be used once per fight.")
                return None
            self.items_used[key] = 1
            damage, evolves_into = self.THUNDER_ITEMS[key]
            print(f"You call down {item}'s lightning!")
            self._hit_all(damage)
            self._count_thunder_use(item, evolves_into)
            return "end_turn"

        return None

    def _hit_all(self, damage):
        for e in self.enemies:
            if e.is_alive():
                self._hit_enemy(e, damage, "item")

    def _count_thunder_use(self, item, evolves_into):
        """Thunder items upgrade after THUNDER_EVOLVE_USES lifetime uses (tracked in item_state)"""
        if not evolves_into:
            return
        uses = self.player.item_state.get(item.lower(), 0) + 1
        if uses >= self.THUNDER_EVOLVE_USES:
            self.player.loot[self.player.loot.index(item)] = evolves_into
            self.player.item_state.pop(item.lower(), None)
            print(f"Your {item} crackles with new power — it became a {evolves_into}!")
        else:
            self.player.item_state[item.lower()] = uses

    # --- Defend / enemy turn ------------------------------------------------------------------------

    def player_defend(self):
        """Defend until your next turn: every enemy hit takes your usual Defense % and then a flat
        min(10, max(0, def * 0.75)) less. Searing damage isn't blocked."""
        self.defending = True
        block = DamageCalculator.defend_block(self._live_stats().get('Defense', 0))
        print(f"You take a defensive stance, blocking {number(block)} damage from each hit until your next turn.")

    def enemy_turn(self):
        """Handle the currently-acting enemy's turn"""
        enemy = self._current_enemy()
        print(f"\n[The {self._label(self.current_enemy_index)}'s turn]")

        enemy.defending = False  # last turn's guard drops
        was_charging = enemy.charge
        action = enemy_brain.decide(enemy, self.enemies, self.enemies_can_flee)
        if action == "flee":
            self._enemy_flees(enemy)
            self.advance_turn()
            return
        if action == "release":
            enemy.charge = 0
            self._charged_attack(enemy)
        elif action == "charge":
            enemy.charge = CHARGE_BIDING
            line = random.choice([f"The {enemy.name} bides...", f"The {enemy.name} is smiling wickedly..."])
            print(f"{line} (a charged attack is coming)")
        elif action == "defend":
            enemy.defending = True
            if DamageCalculator.enemy_defend_block(enemy.stats.get('Defense', 0)):
                print(f"The {enemy.name} raises its guard.")
            else:
                print(f"The {enemy.name} tries to guard itself... recklessly.")
        elif action == "heal":
            self._enemy_heal(enemy)
        else:
            self.enemy_attack(enemy)
        if was_charging == CHARGE_BIDING:
            enemy.charge = CHARGE_READY  # its in-between move is done: the charged hit is next

        # Corruption: max(current_hp * 0.04, corr, 3) searing damage at the end of its turn, then corr grows by 1
        if enemy.corruption > 0 and enemy.hp > 0:
            corruption_damage = DamageCalculator.corruption_tick_damage(enemy.hp, enemy.corruption)
            enemy.hp = max(0, round(enemy.hp - corruption_damage))
            enemy.corruption += 1
            print(f"Corruption burns the {enemy.name} for {number(corruption_damage)} damage!")
            if enemy.hp <= 0:
                print(f"The {enemy.name} is consumed by corruption!")
                self._check_victory()

        self.advance_turn()

    def enemy_attack(self, enemy, scale=1.0, bonus=0):
        """Handle one enemy attacking the player using patch notes system. `scale` multiplies the hit
        (charged attacks), `bonus` adds flat damage (counters) — for a -Attack enemy the bonus lands
        alongside its siphon, even when its hit itself does 0."""
        damage, effects = DamageCalculator.calculate_enemy_damage(enemy.stats, enemy.name)
        if damage > 0:
            damage = damage * scale + bonus
        elif bonus > 0 and any(kind == "leech_on_hit" for kind, _ in effects):
            damage = bonus

        # Handle enemy special effects
        enemy_unavoidable = False
        leech_amount = 0
        for effect_type, value in effects:
            if effect_type == "leech_on_hit":
                leech_amount = value
            elif effect_type == "curse_player_stat":
                # Enemy with negative luck curses player stats
                self.apply_curse_to_player(value)
                print(f"The {enemy.name}'s attack curses you, reducing a random stat by {value}!")
            elif effect_type == "unavoidable":
                # -Speed: enemy attacks cannot be dodged
                enemy_unavoidable = True

        if damage <= 0:
            if leech_amount > 0:
                self.player.take_damage(leech_amount)
                enemy.hp = min(enemy.max_hp, round(enemy.hp + leech_amount))
                print(f"The {enemy.name} siphons {number(leech_amount)} HP from you!")
                self._check_player_defeated()
            else:
                print(f"The {enemy.name} fails to attack effectively!")
            return

        # Apply damage to player using their defensive stats
        final_damage, counter_effects = DamageCalculator.calculate_damage_taken(
            damage, self._live_stats(), self.player_dodge_bonus,
            unavoidable=enemy_unavoidable, max_hp=self.player.max_hp
        )

        # Defending: a flat block on top of the Defense % already applied above
        if self.defending and final_damage > 0:
            block = DamageCalculator.defend_block(self._live_stats().get('Defense', 0))
            if block > 0:
                self.tally["block"] += min(block, final_damage)
                final_damage = round(max(0, final_damage - block), 2)
                print(f"Your guard blocks {number(block)} damage!")

        # Dodge means no damage occurs at all — it's mutually exclusive with counter/reflect
        # (calculate_damage_taken returns early on dodge, so it's never combined with them)
        for effect_type, value in counter_effects:
            if effect_type == "dodged":
                print("You dodge the enemy's attack!")
                say("evade", enemy=enemy.name)
                return

        # Apply the hit first — damage lands before any reaction to it
        if final_damage > 0:
            self.player.take_damage(final_damage)
            print(f"The {enemy.name} deals {number(final_damage)} damage to you!")

            # -Attack: leeches HP from the player and heals itself by the same amount
            if leech_amount > 0:
                self.player.take_damage(leech_amount)
                enemy.hp = min(enemy.max_hp, round(enemy.hp + leech_amount))
                print(f"The {enemy.name} leeches {number(leech_amount)} HP from you!")

            self._check_player_defeated()

        # Reactions to being hit — counter-attack and reflect — happen after
        for effect_type, value in counter_effects:
            if effect_type == "counter_attack":
                print("You counter-attack!")
                counter_damage = random.randint(2, 6)
                enemy.hp = max(0, round(enemy.hp - counter_damage))
                print(f"Your counter deals {counter_damage} damage!")
                if enemy.hp <= 0:
                    print(f"The {enemy.name} is defeated by your counter!")
                    self._check_victory()
                    return
            elif effect_type == "reflect_damage":
                # Player reflects damage back (from negative defence)
                enemy.hp = max(0, round(enemy.hp - value))
                print(f"You reflect {number(value)} damage back to the {enemy.name}!")
                if enemy.hp <= 0:
                    print(f"The {enemy.name} is defeated by reflected damage!")
                    self._check_victory()
                    return

    def _charged_attack(self, enemy):
        """The charged hit: Attack * 1.5, or for a -Attack enemy its usual leeching hit plus 1.3x the
        siphon as searing damage (the siphon itself stays the same)"""
        print(f"The {enemy.name} unleashes its charged attack!")
        attack = enemy.stats.get('Attack', 0)
        if attack >= 0:
            self.enemy_attack(enemy, scale=DamageCalculator.CHARGE_MULTIPLIER)
            return
        self.enemy_attack(enemy)
        if self.player.is_alive():
            sear = round(DamageCalculator.siphon_amount(attack) * DamageCalculator.CHARGE_SIPHON_SEAR)
            self.player.take_damage(sear)
            print(f"Dark energy sears you for {sear} HP!")
            self._check_player_defeated()

    def _enemy_heal(self, healer):
        """A support member patches up a hurt ally (enemy_brain.heal_target) for 12% of its max HP"""
        alive = [e for e in self.enemies if e.is_alive()]
        target = enemy_brain.heal_target(healer, alive)
        if target is None:
            self.enemy_attack(healer)
            return
        label = self._label(self.enemies.index(target))
        chance = DamageCalculator.enemy_heal_chance(healer.stats.get('Luck', 0), healer.stats.get('Speed', 0))
        if BRAIN.uniform(0, 100) >= chance:
            print(f"The {healer.name} tries to patch up the {label}, but fumbles it.")
            return
        before = target.hp
        target.hp = min(target.max_hp, round(target.hp + max(1, target.max_hp * DamageCalculator.ENEMY_HEAL_SHARE)))
        print(f"The {healer.name} patches up the {label} for {number(target.hp - before)} HP!")

    def _enemy_flees(self, enemy):
        """It runs: gone from the fight, maybe dropping something (30%: gold or loot, a coin flip)"""
        enemy.fled = True
        self.fled_count += 1
        drop = self._flee_drop()
        text = fled_line(enemy.name, drop, self._live_stats().get('Charisma', 0))
        if text:
            print(f"  » {text}")
        else:
            print(f"The {enemy.name} flees the fight!" + (f" It dropped {drop}." if drop else ""))
        self._check_victory()

    def _flee_drop(self):
        """What a fleeing enemy leaves behind, as text ("5 gold", "Dagger"), or None"""
        if BRAIN.uniform(0, 100) >= DamageCalculator.FLEE_DROP_CHANCE:
            return None
        if BRAIN.random() < 0.5:
            gold = BRAIN.randint(*DamageCalculator.FLEE_DROP_GOLD)
            self.flee_gold += gold
            return f"{gold} gold"
        from items.items_data import get_droppable_items
        items = get_droppable_items()
        if not items:
            return None
        names, weights = zip(*items)
        item = BRAIN.choices(names, weights=[max(1, w) for w in weights], k=1)[0]
        self.flee_loot.append(item)
        return item

    def apply_debuff_to_enemy(self, target, debuff_amount):
        """-Magic cursed spell benefit: push one random non-zero enemy stat toward 0 — the same logic
        as an enemy's -Luck curse on you (apply_curse_to_player): a positive stat drops (min 0), a
        negative one rises (max 0), so its negative-stat mechanic weakens too"""
        curseable_stats = ['Attack', 'Speed', 'Defense', 'Luck']
        available_stats = [s for s in curseable_stats if target.stats.get(s, 0) != 0]
        if available_stats:
            stat = random.choice(available_stats)
            old_val = target.stats[stat]
            if old_val > 0:
                target.stats[stat] = max(0, old_val - debuff_amount)
                print(f"Your curse weakens the {target.name}: {stat} drops from {old_val} to {target.stats[stat]}!")
            else:
                target.stats[stat] = min(0, old_val + debuff_amount)
                print(f"Your curse drags the {target.name}'s {stat} toward nothing: {old_val} → {target.stats[stat]}!")
            if target.stats[stat] == 0:
                self.tally["zeroed"] += 1

    def apply_curse_to_player(self, curse_amount):
        """Apply stat curse from enemy negative luck — temporary, reversed after combat"""
        player_stats = self._live_stats()
        curseable_stats = ['Strength', 'Agility', 'Intelligence', 'Defense', 'Magic', 'Luck']
        # All non-zero stats can be cursed
        available_stats = [s for s in curseable_stats if player_stats.get(s, 0) != 0]

        if available_stats:
            cursed_stat = random.choice(available_stats)
            old_value = player_stats[cursed_stat]

            if old_value > 0:
                # Positive stat: reduced by curse amount (min 0)
                new_value = max(0, old_value - curse_amount)
            else:
                # Negative stat: pushed toward 0 (max 0)
                new_value = min(0, old_value + curse_amount)

            self.player.stats[cursed_stat] = new_value
            print(f"Your {cursed_stat} is cursed! {old_value} → {new_value}")

    def run_combat(self):
        """Main combat loop"""
        while self.combat_ongoing and self.player.is_alive() and any(e.is_alive() for e in self.enemies):
            if self.current_turn == "player":
                self.player_turn()
            else:
                self.enemy_turn()

        # Restore stats and max HP that were temporarily modified during combat
        self.player.stats = self.original_player_stats
        self.player.max_hp = self.original_player_max_hp
        self.player.current_hp = min(self.player.current_hp, self.player.max_hp)

        # Combat end results
        if not self.player.is_alive():
            print("\n=== DEFEAT ===")
            return "defeat", self.player.current_hp, self.player.current_mana
        elif self.player_fled:
            print("\n=== FLED ===")
            target_desc = self.enemies[0].name if len(self.enemies) == 1 else f"the {self.enemies[0].name} group"
            print(f"You got away from {target_desc}, but gained nothing from the encounter.")
            return "fled", self.player.current_hp, self.player.current_mana
        elif not any(e.is_alive() for e in self.enemies):
            defeated = [e for e in self.enemies if not e.fled]
            if not defeated:
                print("\n=== It got away ===" if len(self.enemies) == 1 else "\n=== They got away ===")
                print("No EXP from a fight that ran off, but you're still standing.")
                return "enemy_fled", self.player.current_hp, self.player.current_mana
            print("\n=== VICTORY ===")
            if len(self.enemies) == 1:
                print(f"You defeated the {self.enemies[0].name}!")
            elif self.fled_count:
                print(f"You defeated {len(defeated)} {self.enemies[0].name}{'s' if len(defeated) > 1 else ''} "
                      f"({self.fled_count} fled)!")
            else:
                count = "both" if len(self.enemies) == 2 else f"all {len(self.enemies)}"
                print(f"You defeated {count} {self.enemies[0].name}s!")
            return "victory", self.player.current_hp, self.player.current_mana
        else:
            print("\n=== Combat over ===")
            return "ended", self.player.current_hp, self.player.current_mana


# Helper function to start combat
def start_combat(player_data, enemy_name, group_size=1, surprise=False, scaling=0, special=False):
    """Initialize and run a combat encounter. Items used up and item progress (Thunder use counts)
    are written back onto player_data — they're the only combat changes that persist besides
    HP/mana, which come back in the return value."""
    from unlocks.unlocks import record
    role = player_data.role
    record("encounter", enemy_name, role=role)
    combat = Combat(player_data, enemy_name, group_size, surprise, scaling, special)
    result = combat.run_combat()
    for kind, amount in combat.tally.items():
        record(kind, amount=amount, role=role)
    if result[0] == "victory" and combat.bonus_gold:
        player_data.gold += combat.bonus_gold
        print(f"You pick up the {combat.bonus_gold} coins your shots knocked loose.")
    player_data.loot = combat.player.loot
    player_data.item_state = combat.player.item_state
    if result[0] != "defeat" and (combat.flee_gold or combat.flee_loot):
        player_data.gold += combat.flee_gold
        player_data.loot.extend(combat.flee_loot)
    return FightResult(*result, fled=combat.fled_count)
