import random
from combat.damage_calculator import DamageCalculator
from combat.combat_player import Player
from enemies.enemies_data import get_enemy_stats, apply_depth_buff, DEATH
from spells.spells_data import get_spell, spell_cost, spell_base_damage, blade_rush_damage, equipment_spell

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

    def __init__(self, name, depth=0):
        self.name = name
        self.stats = apply_depth_buff(get_enemy_stats(name), depth)
        self.max_hp = self._calculate_hp()
        self.hp = self.max_hp
        self.corruption = self.stats.get('Corruption', 0)  # live value — grows by 1 each of its turns
        self.dodge_bonus = 0
        self.initiative = 0

    def _calculate_hp(self):
        if 'HP' in self.stats:
            return self.stats['HP']
        # Fallback calculation if no HP stat
        strength = self.stats.get('Strength', 5)
        defence = self.stats.get('Defence', 5)
        return abs((strength + defence) * 2)

    def is_alive(self):
        return self.hp > 0


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
    COMBAT_USABLE_ITEMS = ["bomb", "timer", "health potion", "mana potion", "dice machine", *THUNDER_ITEMS]
    BERSERKER_ARMOR = "berserker armor"

    def __init__(self, player_data, enemy_name, group_size=1):
        self.player = Player(player_data)
        depth = player_data.distance
        self.enemies = [Enemy(enemy_name, depth) for _ in range(group_size)]

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
        # Snapshots — both restored after combat ends
        self.original_player_stats = dict(self.player.stats)
        self.original_player_max_hp = self.player.max_hp

        print(f"\n=== COMBAT START ===")
        print(f"Player Initiative: {self.player_initiative}")
        for i, enemy in enumerate(self.enemies, 1):
            label = enemy.name if len(self.enemies) == 1 else f"{enemy.name} #{i}"
            print(f"{label} Initiative: {enemy.initiative}")
        if self.current_turn == "player":
            print("You go first!")
        else:
            print(f"{self._current_enemy().name} goes first!")

    def _current_enemy(self):
        return self.enemies[self.current_enemy_index]

    def _build_turn_order(self):
        """[(kind, enemy_index), ...] sorted by initiative, highest first. kind is 'player' or 'enemy'."""
        order = [("player", None, self.player_initiative)]
        for i, enemy in enumerate(self.enemies):
            order.append(("enemy", i, enemy.initiative))
        order.sort(key=lambda entry: entry[2], reverse=True)
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
                print(f"\n--- {'Your' if kind == 'player' else 'Enemy'} turn ---")
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
        if self.bonus_turn:
            self.bonus_turn = False
        elif self.timer_cooldown > 0:
            self.timer_cooldown -= 1
        if self.player_turns_taken > 0:
            self.regenerate_mana()
        self.player_turns_taken += 1

        self._berserker_check()
        self._tick_heal_over_time()

        print(f"\n{self.player.name}'s Turn")
        print(f"Your HP: {self.player.current_hp}/{self.player.max_hp}")
        print(f"Your Mana: {self.player.current_mana}/{self.player.max_mana}")
        for i, enemy in enumerate(self.enemies, 1):
            if enemy.is_alive():
                label = enemy.name if len(self.enemies) == 1 else f"{enemy.name} #{i}"
                print(f"{label} HP: {enemy.hp}/{enemy.max_hp}")

        if self.channel:
            # Channelling (Blade rush) takes the whole turn — no other actions until it ends
            self._continue_channel()
            self.advance_turn()
            return

        while True:
            choice = input("\nChoose action: [1] Physical Attack [2] Spells & Abilities [3] Defend [4] Skip Turn "
                           "[5] Use Item [6] Flee: ").strip()

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
                    print("There is no escaping Death.")
                    continue
                if not self.attempt_flee():
                    self.advance_turn()  # failed flee costs the turn, same as a missed attack
                break  # successful flee: combat_ongoing is now False, no turn to advance to
            else:
                print("Invalid choice. Please enter 1, 2, 3, 4, 5, or 6.")

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

        print("\nChoose a target:")
        for i in alive:
            e = self.enemies[i]
            print(f"  [{i + 1}] {e.name} ({e.hp}/{e.max_hp} HP)")

        while True:
            choice = input("Target: ").strip()
            try:
                index = int(choice) - 1
            except ValueError:
                index = -1
            if index in alive:
                return index
            print("Invalid choice.")

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
            self.player_fled = True
            self.combat_ongoing = False
            return True

        print("You fail to escape!")
        return False

    # --- Damage the player deals ------------------------------------------------------------------

    def _hit_enemy(self, target, damage, damage_type):
        """Land damage on an enemy and return how much it actually took. Corrupted enemies ignore
        their Defense entirely — corruption is their only protection, and a hit that doesn't clear
        it heals them. Everyone else goes through Defense (physical/spell/item, see
        DamageCalculator.enemy_defence_adjustment), and -Defense can reflect physical hits."""
        if target.corruption > 0:
            dealt, heal = DamageCalculator.corruption_hit(damage, target.corruption)
            if heal > 0:
                target.hp = min(target.max_hp, round(target.hp + heal))
                print(f"Corruption swallows the hit and heals the {target.name} for {round(heal, 1)} HP!")
            else:
                target.hp = max(0, round(target.hp - dealt))
                print(f"You deal {round(dealt)} searing damage to the {target.name}!")
        else:
            dealt, reflected = DamageCalculator.enemy_defence_adjustment(damage, target.stats.get('Defense', 0), damage_type)
            target.hp = max(0, round(target.hp - dealt))
            print(f"You deal {round(dealt)} damage to the {target.name}!")
            if reflected > 0:
                self.player.take_damage(reflected)
                print(f"You take {round(reflected, 1)} reflected damage!")
                self._check_player_defeated()

        if target.hp <= 0:
            print(f"The {target.name} is defeated!")
            self._check_victory()
        return dealt

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
            self.player.heal(heal)
            print(f"You heal {heal} HP from the blow!")

    def player_attack(self):
        """Physical attack on a chosen enemy. Returns True if it landed."""
        target_index = self._choose_target()
        if target_index is None:
            return False
        target = self.enemies[target_index]

        damage, unavoidable = DamageCalculator.calculate_player_damage(self._live_stats())
        landed = False
        dealt = 0

        if damage <= 0:
            print("Your attack completely misses!")
        else:
            dodged, countered = (False, False) if unavoidable else DamageCalculator.roll_dodge(target.dodge_bonus)
            if dodged:
                print(f"The {target.name} dodges your attack!")
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
        if spell.get("once_per_combat") and casts:
            return "used this fight"
        if spell["cost"] == "all":
            return "all your mana"
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

        if spell.get("once_per_combat") and casts:
            print(f"{name} can only be cast once per fight.")
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
            if self._rolled_waste():
                spent = min(self.player.current_mana, int(cost * 1.5))
                print(f"Your focus slips and you waste mana — {name} costs {spent}!")
            self.player.current_mana -= spent

        self.spell_casts[name] = casts + 1
        print(f"You use {name}!")

        if name == "Blade rush":
            self.channel = {"name": name, "turns_left": spell["channel_turns"]}
            self._continue_channel()
        elif name == "Nature's gift":
            self.heal_over_time_turns = spell["heal_turns"]
            self._tick_heal_over_time()
        elif name == "Arrowshot":
            self._cast_arrowshot()
        else:
            self._cast_damage_spell(name, spell, casts, cost, magic, intelligence)
        return "end_turn"

    def _cast_damage_spell(self, name, spell, casts, mana_spent, magic, intelligence):
        cursed = spell["kind"] == "cursed"
        damage = spell_base_damage(name, casts, mana_spent) * DamageCalculator.spell_multiplier(magic, cursed)
        damage += DamageCalculator.intelligence_spell_bonus(damage, intelligence, magic)

        target_index = self._choose_target()
        if target_index is None:
            return
        target = self.enemies[target_index]
        self._hit_enemy(target, damage, "spell")

        if cursed and target.is_alive() and random.randint(1, 100) <= DamageCalculator.cursed_debuff_chance(magic):
            self.apply_debuff_to_enemy(target, DamageCalculator.cursed_debuff_amount(magic))

    def _cast_arrowshot(self):
        """Arrowshot: one magical arrow — its own Agility/Magic formula, dealt as magic damage. It's an
        ability, so spell boosts don't apply, but the -Strength curse does."""
        target_index = self._choose_target()
        if target_index is None:
            return
        print("You loose a magical arrow!")
        dealt = self._hit_enemy(self.enemies[target_index], DamageCalculator.arrowshot_damage(self._live_stats()), "spell")
        if self.player.is_alive():
            self._apply_strength_curse(True, dealt)

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
        """Handle player defending"""
        defence_bonus = random.randint(1, 3)
        print(f"You take a defensive stance, reducing incoming damage by {defence_bonus} for this turn.")
        # Store defence bonus for enemy's attack calculation
        self.temp_defence_bonus = defence_bonus

    def enemy_turn(self):
        """Handle the currently-acting enemy's turn"""
        enemy = self._current_enemy()
        print(f"\n{enemy.name}'s Turn")

        self.enemy_attack(enemy)

        # Corruption: max(current_hp * 0.04, corr, 3) searing damage at the end of its turn, then corr grows by 1
        if enemy.corruption > 0 and enemy.hp > 0:
            corruption_damage = DamageCalculator.corruption_tick_damage(enemy.hp, enemy.corruption)
            enemy.hp = max(0, round(enemy.hp - corruption_damage))
            enemy.corruption += 1
            print(f"Corruption burns the {enemy.name} for {round(corruption_damage, 1)} damage!")
            if enemy.hp <= 0:
                print(f"The {enemy.name} is consumed by corruption!")
                self._check_victory()

        self.advance_turn()

    def enemy_attack(self, enemy):
        """Handle one enemy attacking the player using patch notes system"""
        damage, effects = DamageCalculator.calculate_enemy_damage(enemy.stats, enemy.name)

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
                print(f"The {enemy.name} siphons {leech_amount} HP from you!")
                self._check_player_defeated()
            else:
                print(f"The {enemy.name} fails to attack effectively!")
            return

        # Apply temporary defence bonus if player defended
        if hasattr(self, 'temp_defence_bonus'):
            damage = max(1, damage - self.temp_defence_bonus)
            print(f"Your defence reduces the damage by {self.temp_defence_bonus}!")
            delattr(self, 'temp_defence_bonus')

        # Apply damage to player using their defensive stats
        final_damage, counter_effects = DamageCalculator.calculate_damage_taken(
            damage, self._live_stats(), self.player_dodge_bonus,
            unavoidable=enemy_unavoidable, max_hp=self.player.max_hp
        )

        # Dodge means no damage occurs at all — it's mutually exclusive with counter/reflect
        # (calculate_damage_taken returns early on dodge, so it's never combined with them)
        for effect_type, value in counter_effects:
            if effect_type == "dodged":
                print("You dodge the enemy's attack!")
                return

        # Apply the hit first — damage lands before any reaction to it
        if final_damage > 0:
            self.player.take_damage(final_damage)
            print(f"The {enemy.name} deals {final_damage} damage to you!")

            # -Attack: leeches HP from the player and heals itself by the same amount
            if leech_amount > 0:
                self.player.take_damage(leech_amount)
                enemy.hp = min(enemy.max_hp, round(enemy.hp + leech_amount))
                print(f"The {enemy.name} leeches {leech_amount} HP from you!")

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
                print(f"You reflect {value} damage back to the {enemy.name}!")
                if enemy.hp <= 0:
                    print(f"The {enemy.name} is defeated by reflected damage!")
                    self._check_victory()
                    return

    def apply_debuff_to_enemy(self, target, debuff_amount):
        """-Magic cursed spell benefit: lower one random (positive) enemy stat"""
        curseable_stats = ['Attack', 'Speed', 'Defense', 'Luck']
        available_stats = [s for s in curseable_stats if target.stats.get(s, 0) > 0]
        if available_stats:
            stat = random.choice(available_stats)
            old_val = target.stats[stat]
            target.stats[stat] = max(0, old_val - debuff_amount)
            print(f"Your curse weakens the {target.name}: {stat} drops from {old_val} to {target.stats[stat]}!")

    def apply_curse_to_player(self, curse_amount):
        """Apply stat curse from enemy negative luck — temporary, reversed after combat"""
        player_stats = self._live_stats()
        curseable_stats = ['Strength', 'Agility', 'Intelligence', 'Defence', 'Magic', 'Luck']
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
        print("Your stats have been restored.")

        # Combat end results
        if not self.player.is_alive():
            print("\n=== DEFEAT ===")
            print("Game Over!")
            return "defeat", self.player.current_hp, self.player.current_mana
        elif self.player_fled:
            print("\n=== FLED ===")
            target_desc = self.enemies[0].name if len(self.enemies) == 1 else f"the {self.enemies[0].name} group"
            print(f"You got away from {target_desc}, but gained nothing from the encounter.")
            return "fled", self.player.current_hp, self.player.current_mana
        elif not any(e.is_alive() for e in self.enemies):
            print("\n=== VICTORY ===")
            if len(self.enemies) == 1:
                print(f"You defeated the {self.enemies[0].name}!")
            else:
                print(f"You defeated all {len(self.enemies)} {self.enemies[0].name}s!")
            return "victory", self.player.current_hp, self.player.current_mana
        else:
            print("\n=== COMBAT ENDED ===")
            return "ended", self.player.current_hp, self.player.current_mana


# Helper function to start combat
def start_combat(player_data, enemy_name, group_size=1):
    """Initialize and run a combat encounter. Items used up and item progress (Thunder use counts)
    are written back onto player_data — they're the only combat changes that persist besides
    HP/mana, which come back in the return value."""
    combat = Combat(player_data, enemy_name, group_size)
    result = combat.run_combat()
    player_data.loot = combat.player.loot
    player_data.item_state = combat.player.item_state
    return result
