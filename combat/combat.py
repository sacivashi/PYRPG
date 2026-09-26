import random
import math
from combat.damage_calculator import DamageCalculator
from combat.combat_player import Player
from enemies.enemies_data import get_enemy_stats

# Group encounters: a flat chance any fight is 2-3 of the same enemy type instead of solo.
GROUP_CHANCE = 25  # % chance
GROUP_SIZES = (2, 3)


def roll_group_size():
    """25% chance of facing 2-3 of the same enemy at once; otherwise a solo fight (size 1)."""
    if random.randint(1, 100) <= GROUP_CHANCE:
        return random.choice(GROUP_SIZES)
    return 1


class Enemy:
    """One member of a (possibly solo) enemy group. Each has its own HP, stats (so a debuff
    on one doesn't affect its siblings), corruption tracking, and initiative/dodge_bonus."""

    def __init__(self, name):
        self.name = name
        self.stats = get_enemy_stats(name)
        self.max_hp = self._calculate_hp()
        self.hp = self.max_hp
        self.corruption = self.stats.get('Corruption', 0)
        self.corruption_counter = 0
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
    COMBAT_USABLE_ITEMS = ["Bomb", "Timer"]

    def __init__(self, player_data, enemy_name, group_size=1):
        self.player = Player(player_data)
        self.enemies = [Enemy(enemy_name) for _ in range(group_size)]

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
        self.player_fled = False
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

    def player_turn(self):
        """Handle player's turn with menu options"""
        if self.timer_cooldown > 0:
            self.timer_cooldown -= 1

        print(f"\n{self.player.name}'s Turn")
        print(f"Your HP: {self.player.current_hp}/{self.player.max_hp}")
        for i, enemy in enumerate(self.enemies, 1):
            if enemy.is_alive():
                label = enemy.name if len(self.enemies) == 1 else f"{enemy.name} #{i}"
                print(f"{label} HP: {enemy.hp}/{enemy.max_hp}")

        while True:
            choice = input("\nChoose action: [1] Physical Attack [2] Magic Attack [3] Defend [4] Skip Turn "
                           "[5] Use Item [6] Flee: ").strip()

            # No save option during combat!
            if choice in ["save", "s"]:
                print("❌ Cannot save during combat!")
                continue

            if choice == "1":
                hit_landed = self.player_attack(is_magic_attack=False)
                if not hit_landed:
                    print("You missed! Turn ends.")
                self.advance_turn()
                break
            elif choice == "2":
                hit_landed = self.player_attack(is_magic_attack=True)
                if not hit_landed:
                    print("Your magic failed! Turn ends.")
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
                break  # "repeat_turn" (Timer): stay on player's turn, no advance_turn()
            elif choice == "6":
                if not self.attempt_flee():
                    self.advance_turn()  # failed flee costs the turn, same as a missed attack
                break  # successful flee: combat_ongoing is now False, no turn to advance to
            else:
                print("Invalid choice. Please enter 1, 2, 3, 4, 5, or 6.")

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
        agility = self.player.get_live_stats()['stats'].get('Agility', 0)
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

    def use_item(self):
        """Consume a combat-usable item from loot. Returns 'end_turn', 'repeat_turn', or None (cancelled/invalid)."""
        available = [item for item in self.player.loot if item in self.COMBAT_USABLE_ITEMS]
        if not available:
            print("You have no usable items.")
            return None

        print("\nUsable items:")
        for i, item in enumerate(available, 1):
            suffix = f" (cooldown: {self.timer_cooldown} more turns)" if item == "Timer" and self.timer_cooldown > 0 else ""
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

        if item == "Bomb":
            alive = [e for e in self.enemies if e.is_alive()]
            for e in alive:
                e.hp = max(0, e.hp - 35)
            self.player.loot.remove("Bomb")
            if len(alive) > 1:
                print(f"You throw a Bomb, dealing 35 damage to all {len(alive)} enemies!")
            else:
                print(f"You throw a Bomb at the {alive[0].name}, dealing 35 damage!")
            for e in alive:
                if e.hp <= 0:
                    print(f"The {e.name} is defeated!")
            if not any(e.is_alive() for e in self.enemies):
                self.combat_ongoing = False
            return "end_turn"

        if item == "Timer":
            if self.timer_cooldown > 0:
                print(f"Timer is on cooldown for {self.timer_cooldown} more turns.")
                return None
            print("Time freezes around you! You act again immediately.")
            self.timer_cooldown = 5
            return "repeat_turn"

        return None

    def player_attack(self, is_magic_attack=False):
        """Handle player attacking a chosen enemy using patch notes damage system"""
        target_index = self._choose_target()
        if target_index is None:
            return False
        target = self.enemies[target_index]

        player_stats = self.player.get_live_stats()['stats']
        player_max_hp = self.player.max_hp
        player_current_hp = self.player.current_hp

        # Calculate damage
        damage, effects, unavoidable = DamageCalculator.calculate_player_damage(
            player_stats, player_max_hp, player_current_hp, is_magic_attack
        )

        # Pre-hit effects: confusion redirects to a different living target if one exists,
        # otherwise it just fails (matches the original solo-fight behavior)
        for effect_type, value in effects:
            if effect_type == "confusion":
                other_targets = [i for i, e in enumerate(self.enemies) if e.is_alive() and i != target_index]
                if other_targets:
                    target_index = random.choice(other_targets)
                    target = self.enemies[target_index]
                    print(f"You are confused and attack the {target.name} instead!")
                else:
                    print("You are confused and attack the wrong target!")
                    return False

        # Apply magic max HP drain — reduces max_hp, current_hp capped to match
        for effect_type, value in effects:
            if effect_type == "hp_drain":
                self.player.max_hp = max(1, self.player.max_hp - value)
                self.player.current_hp = min(self.player.current_hp, self.player.max_hp)
                print(f"Cursed magic drains {value} max HP! ({self.player.current_hp}/{self.player.max_hp})")

        if damage <= 0:
            print("Your attack completely misses!")
            return False

        # Apply target's defensive calculations (dodge roll skipped entirely if unavoidable)
        final_damage, counter_effects = DamageCalculator.calculate_damage_taken(
            damage, target.stats, target.dodge_bonus, is_enemy=True, unavoidable=unavoidable
        )

        for effect_type, value in counter_effects:
            if effect_type == "dodged":
                print(f"The {target.name} dodges your attack!")
                return False

        # Apply damage to target — corruption enemies heal from player hits
        if target.corruption > 0:
            # min(max_hp * 0.01, (damage_taken + corr) * 0.03)
            heal = min(target.max_hp * 0.01, (final_damage + target.corruption) * 0.03)
            target.hp = min(target.max_hp, round(target.hp + heal))
            print(f"Your attack heals the {target.name} for {round(heal, 1)} HP (Corruption)!")
        else:
            target.hp = max(0, round(target.hp - final_damage))
            print(f"You deal {final_damage} damage to the {target.name}!")

        # Post-hit effects
        missing_hp = player_max_hp - player_current_hp
        self_damage = next((v for t, v in effects if t == "self_damage_after_hit"), 0)
        for effect_type, value in effects:
            if effect_type == "heal_on_hit":
                # min(int(sqrt(missing_hp + damage_done) * 0.5), int(self_damage * 0.75))
                heal_amount = min(
                    int(math.sqrt(missing_hp + final_damage) * 0.5),
                    int(self_damage * 0.75)
                )
                self.player.heal(heal_amount)
                print(f"You heal {heal_amount} HP from your attack!")
            elif effect_type == "enemy_stat_debuff":
                self.apply_debuff_to_enemy(target, value)
                print(f"Your cursed magic debuffs the {target.name}!")
            elif effect_type == "self_damage_after_hit":
                self.player.take_damage(value)
                print(f"Your attack costs you {value} HP!")

        # Handle counter effects
        for effect_type, value in counter_effects:
            if effect_type == "reflect_damage":
                self.player.take_damage(value)
                print(f"You take {value} reflected damage!")
            elif effect_type == "counter_attack":
                counter_damage = random.randint(1, 5)
                self.player.take_damage(counter_damage)
                print(f"Enemy counters for {counter_damage} damage!")

        # Check if the target is defeated
        if target.hp <= 0:
            print(f"The {target.name} is defeated!")
            if not any(e.is_alive() for e in self.enemies):
                self.combat_ongoing = False

        return True

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

        # Corruption: enemy takes max(current_hp * 0.08, max(++corr, 5)) damage at end of its turn
        if enemy.corruption > 0 and enemy.hp > 0:
            enemy.corruption_counter += enemy.corruption  # ++corr: increment before use
            corruption_damage = max(enemy.hp * 0.08, max(enemy.corruption_counter, 5))
            enemy.hp = max(0, round(enemy.hp - corruption_damage))
            print(f"Corruption burns the {enemy.name} for {round(corruption_damage, 1)} damage!")
            if enemy.hp <= 0:
                print(f"The {enemy.name} is consumed by corruption!")
                if not any(e.is_alive() for e in self.enemies):
                    self.combat_ongoing = False

        self.advance_turn()

    def enemy_attack(self, enemy):
        """Handle one enemy attacking the player using patch notes system"""
        # Calculate enemy damage using patch notes system
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
                if not self.player.is_alive():
                    print("You have been defeated!")
                    self.combat_ongoing = False
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
            damage, self.player.get_live_stats()['stats'], self.player_dodge_bonus,
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

            # Check if player is defeated
            if not self.player.is_alive():
                print("You have been defeated!")
                self.combat_ongoing = False

        # Reactions to being hit — counter-attack and reflect — happen after
        for effect_type, value in counter_effects:
            if effect_type == "counter_attack":
                print("You counter-attack!")
                counter_damage = random.randint(2, 6)
                enemy.hp = max(0, round(enemy.hp - counter_damage))
                print(f"Your counter deals {counter_damage} damage!")
                if enemy.hp <= 0:
                    print(f"The {enemy.name} is defeated by your counter!")
                    if not any(e.is_alive() for e in self.enemies):
                        self.combat_ongoing = False
                    return
            elif effect_type == "reflect_damage":
                # Player reflects damage back (from negative defence)
                enemy.hp = max(0, round(enemy.hp - value))
                print(f"You reflect {value} damage back to the {enemy.name}!")
                if enemy.hp <= 0:
                    print(f"The {enemy.name} is defeated by reflected damage!")
                    if not any(e.is_alive() for e in self.enemies):
                        self.combat_ongoing = False
                    return

    def apply_debuff_to_enemy(self, target, debuff_amount):
        """Apply stat debuff to the target enemy from player's -Magic benefit"""
        curseable_stats = ['Attack', 'Speed', 'Defense', 'Luck']
        available_stats = [s for s in curseable_stats if target.stats.get(s, 0) > 0]
        if available_stats:
            stat = random.choice(available_stats)
            old_val = target.stats[stat]
            target.stats[stat] = max(0, old_val - debuff_amount)
            print(f"The {target.name}'s {stat} drops from {old_val} to {target.stats[stat]}!")

    def apply_curse_to_player(self, curse_amount):
        """Apply stat curse from enemy negative luck — temporary, reversed after combat"""
        player_stats = self.player.get_live_stats()['stats']
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
            return "defeat", self.player.current_hp
        elif self.player_fled:
            print("\n=== FLED ===")
            target_desc = self.enemies[0].name if len(self.enemies) == 1 else f"the {self.enemies[0].name} group"
            print(f"You got away from {target_desc}, but gained nothing from the encounter.")
            return "fled", self.player.current_hp
        elif not any(e.is_alive() for e in self.enemies):
            print("\n=== VICTORY ===")
            if len(self.enemies) == 1:
                print(f"You defeated the {self.enemies[0].name}!")
            else:
                print(f"You defeated all {len(self.enemies)} {self.enemies[0].name}s!")
            return "victory", self.player.current_hp
        else:
            print("\n=== COMBAT ENDED ===")
            return "ended", self.player.current_hp


# Helper function to start combat
def start_combat(player_data, enemy_name, group_size=1):
    """Initialize and run a combat encounter"""
    combat = Combat(player_data, enemy_name, group_size)
    return combat.run_combat()
