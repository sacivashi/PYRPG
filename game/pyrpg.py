import sys
import os

# Add the project root to Python path so we can import game_data modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from game_data.data_inputs.input_name.input_name import InputName
from game_data.combat.combat import start_combat
from game_data.data_actions.extracts.enemies_extract import get_enemy_names
from game_data.data_actions.saves.player_data_save import save_new_player
from game_data.data_actions.extracts.player_data_extract import NewPlayer


class PYRPG:
    def __init__(self):
        # Initialize player
        self.player_data = InputName.input_name()
        
        # Main game loop
        self.main_menu()
    
    def main_menu(self):
        """Main game menu with options"""
        while True:
            print(f"\n=== PYRPG - Main Menu ===")
            print(f"Welcome, {self.player_data.name}!")
            print("[1] Enter Combat")
            print("[2] View Stats") 
            print("[3] Save Game")
            print("[4] Exit Game")
            
            choice = input("\nChoose an option: ").strip()
            
            if choice == "1":
                self.enter_combat()
            elif choice == "2":
                self.view_stats()
            elif choice == "3":
                self.save_game()
            elif choice == "4":
                print("Thanks for playing PyRPG!")
                break
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")
    
    def enter_combat(self):
        """Start a combat encounter"""
        enemy_name = get_enemy_names()
        print(f"\nA wild {enemy_name} appears!")
        
        # Auto-save before risky combat
        print("💾 Auto-saving before combat...")
        self.auto_save_player_state()
        
        result = start_combat(self.player_data, enemy_name)
        
        if result == "victory":
            print("You gained experience and loot!")
        elif result == "defeat":
            print("Game Over! Returning to main menu...")
            # In a full game, you might want to handle this differently
        
        input("\nPress Enter to continue...")
    
    def view_stats(self):
        """Display player stats"""
        print(f"\n=== Player Stats ===")
        print(f"Name: {self.player_data.name}")
        print(f"Role: {self.player_data.role.capitalize()}")
        print(f"Level: {self.player_data.level}")
        print(f"HP: {self.player_data.hp}")
        print("Stats:")
        for stat, value in self.player_data.stats.items():
            print(f"  {stat}: {value}")
        
        input("\nPress Enter to continue...")

    def _do_save(self):
        """Shared save logic used by save_game and auto_save"""
        player = NewPlayer.__new__(NewPlayer)
        player.name = self.player_data.name
        player.role = self.player_data.role
        player.level = self.player_data.level
        player.hp = self.player_data.hp
        player.stats = self.player_data.stats
        save_new_player(player)

    def save_game(self):
        """Save the current game state"""
        print("\n=== Saving Game ===")
        self._do_save()
        print("Game saved successfully!")
        input("\nPress Enter to continue...")

    def auto_save_player_state(self):
        """Auto-save before risky actions like combat"""
        self._do_save()
        print("Auto-save complete.")


if __name__ == "__main__":
    PYRPG()
