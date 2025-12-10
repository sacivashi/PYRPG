import random
from game_data.combat.damage_calculator import DamageCalculator
from game_data.data_actions.extracts.player_data_extract import Player
from game_data.data_actions.extracts.enemies_extract import get_enemy_stats

print(abs(-1))

class Combat:
    def __init__(self, player_data, enemy_name):
        self.player = Player(player_data)
        self.enemy_name = enemy_name
        self.enemy_stats = get_enemy_stats(enemy_name)
        self.enemy_hp = self.calculate_enemy_hp()
        self.enemy_max_hp = self.enemy_hp
        
        # Calculate initiative for turn order
        self.player_initiative, self.player_dodge_bonus = self.calculate_initiative(self.player.get_live_stats()['stats'])
        self.enemy_initiative, self.enemy_dodge_bonus = self.calculate_initiative(self.enemy_stats)
        
        # Track whose turn it is
        self.current_turn = "player" if self.player_initiative >= self.enemy_initiative else "enemy"
        self.combat_ongoing = True
        self.allow_saves = False  # Block saves during combat
        
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
        
        # Calculate damage using new system
        damage, effects, unavoidable = DamageCalculator.calculate_player_damage(
            player_stats, player_max_hp, is_magic_attack
        )
        
        # Handle special effects first
        for effect_type, value in effects:
            if effect_type == "self_damage":
                self.player.take_damage(value)
                print(f"You take {value} damage from your failed attack!")
                return False  # Attack failed, turn ends
            elif effect_type == "confusion":
                print("You are confused and attack the wrong target!")
                return False  # Confused attack, turn ends
            elif effect_type == "heal_on_hit":
                # This will be applied after successful hit
                pass
        
        if damage <= 0:
            print("Your attack completely misses!")
            return False  # No damage dealt, turn ends
        
        # Apply enemy's defensive calculations with their dodge bonus
        final_damage, counter_effects = DamageCalculator.calculate_damage_taken(
            damage, self.enemy_stats, self.enemy_dodge_bonus
        )
        
        # Check if enemy dodged (unless unavoidable)
        for effect_type, value in counter_effects:
            if effect_type == "dodged" and not unavoidable:
                print("The enemy dodges your attack!")
                return False  # Attack dodged, turn ends
        
        # Apply damage to enemy
        self.enemy_hp = max(0, self.enemy_hp - final_damage)
        print(f"You deal {final_damage} damage to the {self.enemy_name}!")
        
        # Apply healing effect from negative strength (if any)
        for effect_type, value in effects:
            if effect_type == "heal_on_hit":
                self.player.heal(value)
                print(f"You heal {value} HP from your attack!")
        
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
        
        return True  # Successful attack
    
    def player_defend(self):
        """Handle player defending"""
        defence_bonus = random.randint(1, 3)
        print(f"You take a defensive stance, reducing incoming damage by {defence_bonus} for this turn.")
        # Store defence bonus for enemy's attack calculation
        self.temp_defence_bonus = defence_bonus
    
    def enemy_turn(self):
        """Handle enemy's turn"""
        print(f"\n{self.enemy_name}'s Turn")
        
        # Simple enemy AI - always attacks for now
        self.enemy_attack()
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
    
    def apply_curse_to_player(self, curse_amount):
        """Apply stat curse from enemy negative luck"""
        # Randomly choose a stat to curse (following patch notes logic)
        player_stats = self.player.get_live_stats()['stats']
        curseable_stats = ['Strength', 'Agility', 'Intelligence', 'Defence', 'Magic', 'Luck']
        
        # Filter out stats that are already negative (as per patch notes)
        available_stats = [stat for stat in curseable_stats if player_stats.get(stat, 0) > 0]
        
        if available_stats:
            cursed_stat = random.choice(available_stats)
            old_value = player_stats[cursed_stat]
            new_value = max(0, old_value - curse_amount)  # Can't go below 0
            
            # Update the player's stats
            self.player.stats[cursed_stat] = new_value
            print(f"Your {cursed_stat} is cursed! {old_value} → {new_value}")
    
    def run_combat(self):
        """Main combat loop"""
        while self.combat_ongoing and self.player.is_alive() and self.enemy_hp > 0:
            if self.current_turn == "player":
                self.player_turn()
            else:
                self.enemy_turn()
        
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
