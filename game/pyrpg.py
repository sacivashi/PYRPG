import random
import sys
import os

# Add the project root to Python path so we can import top-level modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from players.input_name import InputName
from combat.combat import start_combat
from enemies.enemies_data import get_enemy_names
from players.save import put_new_player
from combat.combat_player import Player


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
            print("[3] Manage Loot")
            print("[4] Save Game")
            print("[5] Exit Game")

            choice = input("\nChoose an option: ").strip()

            if choice == "1":
                self.enter_combat()
            elif choice == "2":
                self.view_stats()
            elif choice == "3":
                self.manage_loot()
            elif choice == "4":
                self.save_game()
            elif choice == "5":
                print("Thanks for playing PyRPG!")
                break
            else:
                print("Invalid choice. Please enter 1, 2, 3, 4, or 5.")
    
    def enter_combat(self):
        """Start a combat encounter"""
        enemy_name = get_enemy_names()
        print(f"\nA wild {enemy_name} appears!")
        
        # Auto-save before risky combat
        print("💾 Auto-saving before combat...")
        self.auto_save_player_state()
        
        result = start_combat(self.player_data, enemy_name)
        
        if result == "victory":
            gold_reward = self.calculate_gold_reward()
            self.player_data.gold += gold_reward
            print(f"You gained {gold_reward} gold!")
        elif result == "defeat":
            print("Game Over! Returning to main menu...")
            # In a full game, you might want to handle this differently
        
        input("\nPress Enter to continue...")

    def calculate_gold_reward(self):
        """Gold scales with Luck: low = max(5, luck * 0.42), high = max(low + 5, luck * 1.8)"""
        luck = self.player_data.stats.get('Luck', 0)
        low = max(5, luck * 0.42)
        high = max(low + 5, luck * 1.8)
        return random.randint(int(low), int(high))

    def view_stats(self):
        """Display player stats"""
        effective_stats = Player.apply_equipment(self.player_data.stats, self.player_data.equipped)
        print(f"\n=== Player Stats ===")
        print(f"Name: {self.player_data.name}")
        print(f"Role: {self.player_data.role.capitalize()}")
        print(f"Level: {self.player_data.level}")
        print(f"HP: {self.player_data.hp}/{self.player_data.max_hp}")
        print(f"Gold: {self.player_data.gold}")
        print(f"Loot: {self.player_data.loot if self.player_data.loot else 'None'}")
        print(f"Equipped: {self.player_data.equipped or 'Nothing'}")
        print("Stats:")
        for stat, value in effective_stats.items():
            print(f"  {stat}: {value}")

        input("\nPress Enter to continue...")

    def manage_loot(self):
        """Equip or unequip an item from loot"""
        print(f"\n=== Loot ===")
        print(f"Gold: {self.player_data.gold}")
        print(f"Equipped: {self.player_data.equipped or 'Nothing'}")

        if not self.player_data.loot:
            print("You have no loot.")
            input("\nPress Enter to continue...")
            return

        print("Inventory:")
        for i, item_name in enumerate(self.player_data.loot, 1):
            print(f"  [{i}] {item_name}")
        print("  [0] Unequip / Cancel")

        choice = input("\nChoose an item to equip (0 to unequip/cancel): ").strip()

        if choice == "0":
            if self.player_data.equipped:
                self.player_data.equipped = None
                print("Unequipped.")
                self._apply_equipment_hp_change()
            input("\nPress Enter to continue...")
            return

        try:
            index = int(choice) - 1
            if index < 0 or index >= len(self.player_data.loot):
                raise ValueError
        except ValueError:
            print("Invalid choice.")
            input("\nPress Enter to continue...")
            return

        self.player_data.equipped = self.player_data.loot[index]
        print(f"Equipped {self.player_data.equipped}.")
        self._apply_equipment_hp_change()
        input("\nPress Enter to continue...")

    def _apply_equipment_hp_change(self):
        """Recompute max HP after equipping/unequipping. Clamp only — no free heal from gear."""
        effective_stats = Player.apply_equipment(self.player_data.stats, self.player_data.equipped)
        new_max_hp = Player.calculate_hp(effective_stats)
        self.player_data.hp = min(self.player_data.hp, new_max_hp)
        self.player_data.max_hp = new_max_hp

    def _do_save(self):
        """Shared save logic used by save_game and auto_save"""
        player = Player(self.player_data)
        put_new_player(player)

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
