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
from items.items_data import get_item_stats, get_buyable_items


class PYRPG:
    def __init__(self):
        # Initialize player
        self.player_data = InputName.input_name()
        self.saving_enabled = self._ask_saving_preference()
        self.in_town = True
        self.distance = 0
        self.failed_attempts = 0

        # Main game loop
        self.main_menu()

    def _ask_saving_preference(self):
        """Ask once per session whether auto-saves should write to the save file at all"""
        print(f"\nWelcome, {self.player_data.name}!")
        choice = input("Would you like your progress to be auto-saved this session? (Y/n): ").strip().lower()
        return choice != "n"

    def main_menu(self):
        """Main game loop — dispatches to the town or wild menu depending on location"""
        while True:
            action = self.town_menu() if self.in_town else self.wild_menu()
            if action == "exit":
                print("Thanks for playing PyRPG!")
                break

    def town_menu(self):
        """Menu shown while in town"""
        print(f"\n=== Town ===")
        print(f"Welcome, {self.player_data.name}!")
        print("[1] Travel Outside")
        print("[2] Rest")
        print("[3] Shop")
        print("[4] View Stats")
        print("[5] Manage Loot")
        print("[6] Save Game")
        print("[7] Exit Game")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            self.travel_outside()
        elif choice == "2":
            self.full_rest()
        elif choice == "3":
            self.shop()
        elif choice == "4":
            self.view_stats()
        elif choice == "5":
            self.manage_loot()
        elif choice == "6":
            self.save_game()
        elif choice == "7":
            return "exit"
        else:
            print("Invalid choice. Please enter a number between 1 and 7.")

    def wild_menu(self):
        """Menu shown while out in the wild"""
        print(f"\n=== Out in the Wild ===")
        print(f"Distance from town: {self.distance}")
        print("[1] Explore")
        print("[2] Rest")
        print("[3] Return to Town")
        print("[4] View Stats")
        print("[5] Manage Loot")
        print("[6] Save Game")
        print("[7] Exit Game")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            self.explore()
        elif choice == "2":
            self.rest()
        elif choice == "3":
            self.return_to_town()
        elif choice == "4":
            self.view_stats()
        elif choice == "5":
            self.manage_loot()
        elif choice == "6":
            self.save_game()
        elif choice == "7":
            return "exit"
        else:
            print("Invalid choice. Please enter a number between 1 and 7.")

    def travel_outside(self):
        """Leave town and start a new trip into the wild"""
        print("\nYou leave the safety of town...")
        self.in_town = False
        self.distance = 0
        self.failed_attempts = 0

    def explore(self):
        """Venture further out, increasing distance from town, and risk a combat encounter"""
        self.distance += 1
        self.enter_combat()

    def return_to_town(self):
        """Attempt to return to town; failing raises the odds for the next attempt but triggers combat"""
        return_chance = min(100, max(0, 30 - self.distance) + self.failed_attempts * 10)
        roll = random.randint(1, 100)

        print(f"\nYou attempt to return to town... ({return_chance}% chance of success)")

        if roll <= return_chance:
            print("You make it back to town safely!")
            self.in_town = True
            self.distance = 0
            self.failed_attempts = 0
            input("\nPress Enter to continue...")
        else:
            print("You lose your way and are ambushed!")
            self.failed_attempts += 1
            self.enter_combat()

    REST_COST = 10

    def full_rest(self):
        """Town rest: guaranteed full heal, costs gold"""
        if self.player_data.gold < self.REST_COST:
            print(f"\nYou need {self.REST_COST} gold to rest here, but you only have {self.player_data.gold}.")
            input("\nPress Enter to continue...")
            return

        self.player_data.gold -= self.REST_COST
        self.player_data.hp = self.player_data.max_hp
        print(f"\nYou pay {self.REST_COST} gold and rest fully, recovering all your HP.")
        print(f"HP: {self.player_data.hp}/{self.player_data.max_hp}")
        input("\nPress Enter to continue...")

    SHOP_STOCK_SIZE = 4
    REROLL_BASE_COST = 5
    REROLL_COST_STEP = 5

    def shop(self):
        """Buy from a rotating stock of random items; reroll the stock for a growing gold cost"""
        stock = self._roll_shop_stock()
        reroll_cost = self.REROLL_BASE_COST

        while True:
            print(f"\n=== Shop ===")
            print(f"Gold: {self.player_data.gold}")
            for i, (name, price) in enumerate(stock, 1):
                print(f"  [{i}] {name} - {price} gold")
            print(f"  [5] Reroll stock - {reroll_cost} gold")
            print("  [0] Leave shop")

            choice = input("\nChoose an item to buy, 'c' + number to check its stats (e.g. c1), 5 to reroll, or 0 to leave: ").strip()

            if choice == "0":
                return

            if choice.lower().startswith("c"):
                self._check_shop_item_stats(stock, choice[1:].strip())
                continue

            if choice == "5":
                if self.player_data.gold < reroll_cost:
                    print("You don't have enough gold to reroll.")
                    input("\nPress Enter to continue...")
                    continue

                self.player_data.gold -= reroll_cost
                stock = self._roll_shop_stock()
                reroll_cost += self.REROLL_COST_STEP
                print(f"You reroll the shop's stock. Next reroll will cost {reroll_cost} gold.")
                input("\nPress Enter to continue...")
                continue

            try:
                index = int(choice) - 1
                if index < 0 or index >= len(stock):
                    raise ValueError
            except ValueError:
                print("Invalid choice.")
                input("\nPress Enter to continue...")
                continue

            item_name, price = stock[index]
            if self.player_data.gold < price:
                print("You don't have enough gold.")
                input("\nPress Enter to continue...")
                continue

            self.player_data.gold -= price
            self.player_data.loot.append(item_name)
            print(f"Bought {item_name} for {price} gold.")
            input("\nPress Enter to continue...")

    def _roll_shop_stock(self):
        """Pick a random subset of buyable items to stock the shop with"""
        items = get_buyable_items()
        return random.sample(items, min(self.SHOP_STOCK_SIZE, len(items)))

    def _check_shop_item_stats(self, items, index_str):
        """Show an item's stat deltas and price without buying it"""
        try:
            index = int(index_str) - 1
            if index < 0 or index >= len(items):
                raise ValueError
        except ValueError:
            print("Invalid item number.")
            input("\nPress Enter to continue...")
            return

        item_name, price = items[index]
        self._print_item_stats(item_name)
        print(f"  Price: {price} gold")
        input("\nPress Enter to continue...")

    def enter_combat(self):
        """Start a combat encounter"""
        enemy_name = get_enemy_names()
        print(f"\nA wild {enemy_name} appears!")
        
        # Auto-save before risky combat
        print("💾 Auto-saving before combat...")
        self.auto_save_player_state()
        
        result, current_hp = start_combat(self.player_data, enemy_name)
        self.player_data.hp = current_hp

        if result == "victory":
            gold_reward = self.calculate_gold_reward()
            self.player_data.gold += gold_reward
            print(f"You gained {gold_reward} gold!")
        elif result == "defeat":
            self.player_data.hp = max(1, int(self.player_data.max_hp * 0.5))
            print(f"Game Over! You wake up with {self.player_data.hp}/{self.player_data.max_hp} HP.")

        input("\nPress Enter to continue...")

    def rest(self):
        """Attempt to rest: Luck-scaled odds to succeed and heal 30% max HP, otherwise ambushed into combat"""
        luck = self.player_data.stats.get('Luck', 0)
        low = min(35, luck * 0.85)
        high = max(20, luck * 0.95)
        success_chance = random.randint(int(low), int(high))
        roll = random.randint(1, 100)

        print(f"\nYou attempt to rest... ({success_chance}% chance of success)")

        if roll <= success_chance:
            heal_amount = round(self.player_data.max_hp * 0.30)
            self.player_data.hp = min(self.player_data.max_hp, self.player_data.hp + heal_amount)
            print(f"You rest peacefully and recover {heal_amount} HP.")
            print(f"HP: {self.player_data.hp}/{self.player_data.max_hp}")
            input("\nPress Enter to continue...")
        else:
            print("Your rest is interrupted!")
            self.enter_combat()

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
        while True:
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

            choice = input("\nChoose an item to equip, 'c' + number to check its stats (e.g. c1), or 0 to unequip/cancel: ").strip()

            if choice == "0":
                if self.player_data.equipped:
                    self.player_data.equipped = None
                    print("Unequipped.")
                    self._apply_equipment_hp_change()
                input("\nPress Enter to continue...")
                return

            if choice.lower().startswith("c"):
                self._check_loot_stats(choice[1:].strip())
                continue

            try:
                index = int(choice) - 1
                if index < 0 or index >= len(self.player_data.loot):
                    raise ValueError
            except ValueError:
                print("Invalid choice.")
                input("\nPress Enter to continue...")
                continue

            self.player_data.equipped = self.player_data.loot[index]
            print(f"Equipped {self.player_data.equipped}.")
            self._apply_equipment_hp_change()
            input("\nPress Enter to continue...")
            return

    def _check_loot_stats(self, index_str):
        """Show the stat deltas for one item in loot, without equipping it"""
        try:
            index = int(index_str) - 1
            if index < 0 or index >= len(self.player_data.loot):
                raise ValueError
        except ValueError:
            print("Invalid item number.")
            input("\nPress Enter to continue...")
            return

        self._print_item_stats(self.player_data.loot[index])
        input("\nPress Enter to continue...")

    def _print_item_stats(self, item_name):
        """Print an item's non-zero stat deltas"""
        stats = get_item_stats(item_name)
        print(f"\n{item_name}:")
        if stats:
            for stat, value in stats.items():
                if value != 0:
                    sign = "+" if value > 0 else ""
                    print(f"  {stat}: {sign}{value}")
        else:
            print("  No stat data found.")

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
        """Auto-save before risky actions like combat, unless the player opted out this session"""
        if not self.saving_enabled:
            print("Skipping auto-save (disabled for this session).")
            return
        self._do_save()
        print("Auto-save complete.")


if __name__ == "__main__":
    PYRPG()
