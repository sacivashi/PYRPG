import random
import math
from game_data.combat.damage_calculator import DamageCalculator
from game_data.combat.combat_player import Player
from game_data.data_actions.extracts.enemies_extract import get_enemy_stats



class Combat:
    def __init__(self, player_data, enemy_name):
        self.player = Player(player_data)
        self.enemy_name = enemy_name
        self.enemy_stats = get_enemy_stats(enemy_name)
        self.enemy_hp = self.calculate_enemy_hp()
        self.enemy_max_hp = self.enemy_hp
        # Pre-compute passive enemy flags (e.g. -Attack heals when hit)
        _, self.enemy_effects = DamageCalculator.calculate_enemy_damage(self.enemy_stats, enemy_name)
        
        # Calculate initiative for turn order
        self.player_initiative, self.player_dodge_bonus = self.calculate_initiative(self.player.get_live_stats()['stats'])
        self.enemy_initiative, self.enemy_dodge_bonus = self.calculate_initiative(self.enemy_stats)
        
        # Track whose turn it is
        self.current_turn = "player" if self.player_initiative >= self.enemy_initiative else "enemy"
        self.combat_ongoing = True
        self.allow_saves = False  # Block saves during combat
        self.enemy_corruption = self.enemy_stats.get('Corruption', 0)
        self.corruption_counter = 0  # Tracks cumulative corruption damage (corr++)
        # Snapshots — both restored after combat ends
        self.original_player_stats = dict(self.player.stats)
        self.original_player_max_hp = self.player.max_hp
        
        print(f"\n=== COMBAT START ===")
        print(f"Player Initiative: {self.player_initiative}")
        print(f"Enemy Initiative: {self.enemy_initiative}")
        print(f"{'You' if self.current_turn == 'player' else 'Enemy'} go first!")
    
    def calculate_initiative(self, stats):
        """Calculate turn order based on Agility using patch notes specs"""
        agility = stats.get('Agility', 0)
        initiative, dodge_counter_bonus = DamageCalculator.apply_agility_modifier(0, agility)
        
        # Store dodge/counter bonus for negative agility characters
        if agility < 0:
            return initiative, dodge_counter_bonus
        else:
            return initiative + random.randint(0, 5), 0
    
    def calculate_enemy_hp(self):
        """Calculate enemy HP from stats"""
        if 'HP' in self.enemy_stats:
            return self.enemy_stats['HP']
        # Fallback calculation if no HP stat
        strength = self.enemy_stats.get('Strength', 5)
        defence = self.enemy_stats.get('Defence', 5)
        return abs((strength + defence) * 2)
    
    def switch_turns(self):
        """Switch between player and enemy turns"""
        self.current_turn = "enemy" if self.current_turn == "player" else "player"
        print(f"\n--- {'Your' if self.current_turn == 'player' else 'Enemy'} turn ---")
    
    def player_turn(self):
        """Handle player's turn with menu options"""
        print(f"\n{self.player.name}'s Turn")
        print(f"Your HP: {self.player.current_hp}/{self.player.max_hp}")
        print(f"Enemy HP: {self.enemy_hp}/{self.enemy_max_hp}")
        
        while True:
            choice = input("\nChoose action: [1] Physical Attack [2] Magic Attack [3] Defend [4] Skip Turn: ").strip()
            
            # No save option during combat!
            if choice in ["save", "s"]:
                print("❌ Cannot save during combat!")
                continue
            
            if choice == "1":
                hit_landed = self.player_attack(is_magic_attack=False)
                if not hit_landed:
                    print("You missed! Turn ends.")
                self.switch_turns()
                break
            elif choice == "2":
                hit_landed = self.player_attack(is_magic_attack=True)
                if not hit_landed:
                    print("Your magic failed! Turn ends.")
                self.switch_turns()
                break
            elif choice == "3":
                self.player_defend()
                self.switch_turns()
                break
            elif choice == "4":
                print("You skip your turn.")
                self.switch_turns()
                break
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")
    
    def player_attack(self, is_magic_attack=False):
        """Handle player attacking enemy using patch notes damage system"""
        player_stats = self.player.get_live_stats()['stats']
        player_max_hp = self.player.max_hp
        player_current_hp = self.player.current_hp

        # Calculate damage
        damage, effects, unavoidable = DamageCalculator.calculate_player_damage(
            player_stats, player_max_hp, player_current_hp, is_magic_attack
        )

        # Pre-hit effects: confusion cancels the attack
        for effect_type, value in effects:
            if effect_type == "confusion":
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

        # Apply enemy's defensive calculations
        final_damage, counter_effects = DamageCalculator.calculate_damage_taken(
            damage, self.enemy_stats, self.enemy_dodge_bonus, is_enemy=True
        )

        # Check if enemy dodged (unless unavoidable)
        for effect_type, value in counter_effects:
            if effect_type == "dodged" and not unavoidable:
                print("The enemy dodges your attack!")
                return False

        # Apply damage to enemy — corruption enemies heal from player hits
        if self.enemy_corruption > 0:
            heal = min(self.enemy_hp, final_damage * self.enemy_corruption * 1.2) / 100
            self.enemy_hp = min(self.enemy_max_hp, self.enemy_hp + heal)
            print(f"Your attack heals the {self.enemy_name} for {round(heal, 1)} HP (Corruption)!")
        else:
            self.enemy_hp = max(0, self.enemy_hp - final_damage)
            print(f"You deal {final_damage} damage to the {self.enemy_name}!")

        # -Attack enemies heal when hit: min(10, abs(-atk) / 100)% of max HP
        for effect_type, value in self.enemy_effects:
            if effect_type == "enemy_heals_when_hit":
                heal_percent = min(10, value / 100) / 100
                heal_amount = round(self.enemy_max_hp * heal_percent, 1)
                self.enemy_hp = min(self.enemy_max_hp, self.enemy_hp + heal_amount)
                print(f"The {self.enemy_name} heals {heal_amount} HP from your attack!")

        # Post-hit effects
        missing_hp = player_max_hp - player_current_hp
        for effect_type, value in effects:
            if effect_type == "heal_on_hit":
                # int(sqrt(missing_hp + damage_done) + abs(-str * 1.5))
                heal_amount = int(math.sqrt(missing_hp + final_damage) + abs(value * 1.5))
                self.player.heal(heal_amount)
                print(f"You heal {heal_amount} HP from your attack!")
            elif effect_type == "enemy_stat_debuff":
                self.apply_debuff_to_enemy(value)
                print(f"Your cursed magic debuffs the {self.enemy_name}!")
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

        # Check if enemy is defeated
        if self.enemy_hp <= 0:
            print(f"The {self.enemy_name} is defeated!")
            self.combat_ongoing = False

        return True
    
    def player_defend(self):
        """Handle player defending"""
        defence_bonus = random.randint(1, 3)
        print(f"You take a defensive stance, reducing incoming damage by {defence_bonus} for this turn.")
        # Store defence bonus for enemy's attack calculation
        self.temp_defence_bonus = defence_bonus
    
    def enemy_turn(self):
        """Handle enemy's turn"""
        print(f"\n{self.enemy_name}'s Turn")

        self.enemy_attack()

        # Corruption: enemy takes (corr++) damage at end of its turn
        if self.enemy_corruption > 0 and self.enemy_hp > 0:
            self.corruption_counter += self.enemy_corruption
            self.enemy_hp = max(0, self.enemy_hp - self.corruption_counter)
            print(f"Corruption burns the {self.enemy_name} for {self.corruption_counter} damage!")
            if self.enemy_hp <= 0:
                print(f"The {self.enemy_name} is consumed by corruption!")
                self.combat_ongoing = False
                return

        self.switch_turns()
    
    def enemy_attack(self):
        """Handle enemy attacking player using patch notes system"""
        # Calculate enemy damage using patch notes system
        damage, effects = DamageCalculator.calculate_enemy_damage(self.enemy_stats, self.enemy_name)
        
        # Handle enemy special effects
        for effect_type, value in effects:
            if effect_type == "enemy_heals_when_hit":
                # This effect happens when enemy gets hit, not when it attacks
                pass
            elif effect_type == "curse_player_stat":
                # Enemy with negative luck curses player stats
                self.apply_curse_to_player(value)
                print(f"The {self.enemy_name}'s attack curses you, reducing a random stat by {value}!")
        
        if damage <= 0:
            print(f"The {self.enemy_name} fails to attack effectively!")
            return
        
        # Apply temporary defence bonus if player defended
        if hasattr(self, 'temp_defence_bonus'):
            damage = max(1, damage - self.temp_defence_bonus)
            print(f"Your defence reduces the damage by {self.temp_defence_bonus}!")
            delattr(self, 'temp_defence_bonus')
        
        # Apply damage to player using their defensive stats
        final_damage, counter_effects = DamageCalculator.calculate_damage_taken(
            damage, self.player.get_live_stats()['stats'], self.player_dodge_bonus
        )
        
        # Check if player dodged/countered
        for effect_type, value in counter_effects:
            if effect_type == "dodged":
                print("You dodge the enemy's attack!")
                return
            elif effect_type == "counter_attack":
                print("You counter-attack!")
                counter_damage = random.randint(2, 6)
                self.enemy_hp = max(0, self.enemy_hp - counter_damage)
                print(f"Your counter deals {counter_damage} damage!")
                if self.enemy_hp <= 0:
                    print(f"The {self.enemy_name} is defeated by your counter!")
                    self.combat_ongoing = False
                    return
            elif effect_type == "reflect_damage":
                # Player reflects damage back (from negative defence)
                self.enemy_hp = max(0, self.enemy_hp - value)
                print(f"You reflect {value} damage back to the {self.enemy_name}!")
                if self.enemy_hp <= 0:
                    print(f"The {self.enemy_name} is defeated by reflected damage!")
                    self.combat_ongoing = False
                    return
        
        # Apply final damage to player
        if final_damage > 0:
            self.player.take_damage(final_damage)
            print(f"The {self.enemy_name} deals {final_damage} damage to you!")
            
            # Check if player is defeated
            if not self.player.is_alive():
                print("You have been defeated!")
                self.combat_ongoing = False
    
    def apply_debuff_to_enemy(self, debuff_amount):
        """Apply stat debuff to enemy from player's -Magic benefit"""
        curseable_stats = ['Strength', 'Agility', 'Defence', 'Luck']
        available_stats = [s for s in curseable_stats if self.enemy_stats.get(s, 0) > 0]
        if available_stats:
            stat = random.choice(available_stats)
            old_val = self.enemy_stats[stat]
            self.enemy_stats[stat] = max(0, old_val - debuff_amount)
            print(f"The {self.enemy_name}'s {stat} drops from {old_val} to {self.enemy_stats[stat]}!")

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
        while self.combat_ongoing and self.player.is_alive() and self.enemy_hp > 0:
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
            return "defeat"
        elif self.enemy_hp <= 0:
            print("\n=== VICTORY ===")
            print(f"You defeated the {self.enemy_name}!")
            return "victory"
        else:
            print("\n=== COMBAT ENDED ===")
            return "ended"


# Helper function to start combat
def start_combat(player_data, enemy_name):
    """Initialize and run a combat encounter"""
    combat = Combat(player_data, enemy_name)
    return combat.run_combat()
