import random
import sys
import os

# Add the project root to Python path so we can import top-level modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from players.input_name import InputName
from combat.combat import start_combat
from enemies.enemies_data import get_encounter_enemy, get_enemy_difficulty, get_enemy_stats
from players.save import put_new_player
from combat.combat_player import Player
from items.items_data import get_item_stats, get_buyable_items, get_droppable_items, STAT_COLUMNS


class PYRPG:
    def __init__(self):
        # Initialize player and this session's save consent (asked once, inside InputName.input_name())
        self.player_data, self.saving_enabled = InputName.input_name()

        # Main game loop
        self.main_menu()

    def main_menu(self):
        """Main game loop — dispatches to the town or wild menu depending on location"""
        while True:
            action = self.town_menu() if self.player_data.in_town else self.wild_menu()
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
        print(f"Distance from town: {self.player_data.distance}")
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
        self.player_data.in_town = False
        self.player_data.distance = 0
        self.player_data.failed_attempts = 0

    def explore(self):
        """Venture further out, increasing distance from town, and risk a combat encounter"""
        self.player_data.distance += 1
        self.enter_combat()

    def return_to_town(self):
        """Attempt to return to town; failing raises the odds for the next attempt but triggers combat"""
        return_chance = min(100, max(0, 30 - self.player_data.distance) + self.player_data.failed_attempts * 10)
        roll = random.randint(1, 100)

        print(f"\nYou attempt to return to town... ({return_chance}% chance of success)")

        if roll <= return_chance:
            print("You make it back to town safely!")
            self.player_data.in_town = True
            self.player_data.distance = 0
            self.player_data.failed_attempts = 0
            input("\nPress Enter to continue...")
        else:
            print("You lose your way and are ambushed!")
            self.player_data.failed_attempts += 1
            self.enter_combat()

    TOWN_RESPAWN_CHANCE = 55

    def _handle_defeat_respawn(self):
        """On defeat, either wake up back in town (as before) or get knocked backward along
        the current trip and stay in the wild — failed_attempts resets either way, since
        it's a fresh start from wherever you land."""
        self.player_data.failed_attempts = 0

        if self.player_data.distance <= 0 or random.randint(1, 100) <= self.TOWN_RESPAWN_CHANCE:
            self.player_data.in_town = True
            self.player_data.distance = 0
            print(f"Game Over! You wake up back in town with {self.player_data.hp}/{self.player_data.max_hp} HP.")
        else:
            knockback = random.randint(1, self.player_data.distance)
            self.player_data.distance -= knockback
            print(f"Game Over! You're dragged backward {knockback} steps and wake up still "
                  f"out in the wild, at distance {self.player_data.distance}, with "
                  f"{self.player_data.hp}/{self.player_data.max_hp} HP.")

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
    VOUCHER_DISCOUNT = 0.15

    def shop(self):
        """Buy from a rotating stock of random items; reroll the stock for a growing gold cost.
        Bought slots go sold-out until the next reroll. A Voucher in loot gives 15% off and is
        consumed the moment any purchase completes."""
        stock = self._roll_shop_stock()
        reroll_cost = self.REROLL_BASE_COST
        sold_out = set()

        while True:
            has_voucher = "Voucher" in self.player_data.loot
            print(f"\n=== Shop ===")
            print(f"Gold: {self.player_data.gold}")
            if has_voucher:
                print("(Voucher active: 15% off your next purchase)")
            for i, (name, price) in enumerate(stock, 1):
                if (i - 1) in sold_out:
                    print(f"  [{i}] {name} - SOLD OUT")
                else:
                    print(f"  [{i}] {name} - {self._apply_voucher_discount(price, has_voucher)} gold")
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
                sold_out = set()
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

            if index in sold_out:
                print("That item is sold out this visit.")
                input("\nPress Enter to continue...")
                continue

            item_name, price = stock[index]
            final_price = self._apply_voucher_discount(price, has_voucher)
            if self.player_data.gold < final_price:
                print("You don't have enough gold.")
                input("\nPress Enter to continue...")
                continue

            self.player_data.gold -= final_price
            self.player_data.loot.append(item_name)
            sold_out.add(index)
            print(f"Bought {item_name} for {final_price} gold.")
            if has_voucher:
                self.player_data.loot.remove("Voucher")
                print("Your Voucher is used up.")
            input("\nPress Enter to continue...")

    def _apply_voucher_discount(self, price, has_voucher):
        return round(price * (1 - self.VOUCHER_DISCOUNT)) if has_voucher else price

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
        enemy_name = get_encounter_enemy(self._player_power())
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

            exp_reward = self.calculate_exp_reward(enemy_name)
            self.player_data.exp += exp_reward
            print(f"You gained {exp_reward:.1f}% EXP!")
            self._process_level_ups()

            self._roll_for_loot()
        elif result == "defeat":
            self.player_data.hp = max(1, int(self.player_data.max_hp * 0.5))
            self._handle_defeat_respawn()

        input("\nPress Enter to continue...")

    def calculate_rest_chance(self):
        """min(60, max(30, Luck + 15))% for Luck >= 0; max(15, 25 - abs(Luck) * 0.48)% for -Luck"""
        luck = self._effective_stats().get('Luck', 0)
        if luck < 0:
            return round(max(15, 25 - abs(luck) * 0.48), 1)
        return min(60, max(30, luck + 15))

    def _effective_stats(self):
        """Base stats with the equipped item's deltas applied — what the character actually has
        right now. Everything outside combat that reads a stat (rest odds, rewards, encounters,
        max HP) goes through this so gear counts everywhere, not just in fights."""
        return Player.apply_equipment(self.player_data.stats, self.player_data.equipped)

    def _player_power(self):
        """Sum of the player's absolute stats with gear applied — the yardstick encounters are matched against"""
        return sum(abs(int(v)) for v in self._effective_stats().values())

    def _sync_max_hp_after_growth(self):
        """Recompute max HP (gear included) after a permanent stat gain, healing by however much it grew"""
        old_max_hp = self.player_data.max_hp
        new_max_hp = Player.calculate_hp(self._effective_stats())
        self.player_data.hp += max(0, new_max_hp - old_max_hp)
        self.player_data.max_hp = new_max_hp

    def rest(self):
        """Attempt to rest: Luck-based odds to succeed and heal 30% max HP, otherwise ambushed into combat"""
        success_chance = self.calculate_rest_chance()
        roll = random.randint(1, 100)

        print(f"\nYou attempt to rest... ({success_chance:g}% chance of success)")

        if roll <= success_chance:
            heal_amount = round(self.player_data.max_hp * 0.30)
            self.player_data.hp = min(self.player_data.max_hp, self.player_data.hp + heal_amount)
            print(f"You rest peacefully and recover {heal_amount} HP.")
            print(f"HP: {self.player_data.hp}/{self.player_data.max_hp}")
            self._trigger_dice_machine_passive()
            input("\nPress Enter to continue...")
        else:
            print("Your rest is interrupted!")
            self.enter_combat()

    DICE_MACHINE_PROC_CHANCE = 22

    def _trigger_dice_machine_passive(self):
        """While Dice machine is equipped, a successful rest gives each stat an independent
        22% chance to permanently gain a random 1-5 bonus — a gamble on top of its usual
        equip-time reroll."""
        if not self.player_data.equipped or self.player_data.equipped.lower() != "dice machine":
            return

        print("\nThe Dice machine whirs to life...")
        procced = False
        for stat in STAT_COLUMNS:
            if random.randint(1, 100) <= self.DICE_MACHINE_PROC_CHANCE:
                bonus = random.randint(1, 5)
                self.player_data.stats[stat] = self.player_data.stats.get(stat, 0) + bonus
                print(f"  {stat} +{bonus}!")
                procced = True

        if not procced:
            print("  ...nothing happens this time.")
            return

        self._sync_max_hp_after_growth()

    def calculate_gold_reward(self):
        """Gold scales with Luck: low = max(5, luck * 0.42), high = max(low + 5, luck * 1.8)"""
        luck = self._effective_stats().get('Luck', 0)
        low = max(5, luck * 0.42)
        high = max(low + 5, luck * 1.8)
        return random.randint(int(low), int(high))

    LEVEL_UP_POINTS = 5

    def calculate_exp_reward(self, enemy_name):
        """EXP (as % toward next level) scales with enemy difficulty (sum of abs stats),
        +1% per Intelligence point, and decays 5% per player level (floored at 20% of base rate).
        -Magic users earn 15% less."""
        difficulty = get_enemy_difficulty(get_enemy_stats(enemy_name))

        stats = self._effective_stats()
        intelligence = stats.get('Intelligence', 0)
        int_bonus = 1 + max(0, intelligence) * 0.01

        level_penalty = max(0.2, 1 - (self.player_data.level - 1) * 0.05)

        magic_penalty = 0.85 if stats.get('Magic', 0) < 0 else 1

        return (difficulty / 10) * int_bonus * level_penalty * magic_penalty

    def _process_level_ups(self):
        """Roll over 100%+ EXP into level(s), granting ability points to allocate each time"""
        while self.player_data.exp >= 100:
            self.player_data.exp -= 100
            self.player_data.level += 1
            print(f"\n*** LEVEL UP! You are now level {self.player_data.level}! ***")
            self._allocate_level_up_points(self.LEVEL_UP_POINTS)

    def _allocate_level_up_points(self, points):
        """Let the player spend ability points one at a time, raising or lowering any of the
        six stats — lowering costs a point too, same as raising, since going negative opts
        into that stat's debuff/benefit pair rather than being a free do-over."""
        remaining = points
        while remaining > 0:
            print(f"\nAbility points remaining: {remaining}")
            for i, stat in enumerate(STAT_COLUMNS, 1):
                print(f"  [{i}] {stat}: {self.player_data.stats.get(stat, 0)}")

            choice = input("Choose a stat number to raise by 1, or 'l' + number to lower it by 1 (e.g. l3): ").strip()

            lowering = choice.lower().startswith("l")
            index_str = choice[1:].strip() if lowering else choice
            try:
                index = int(index_str) - 1
                if index < 0 or index >= len(STAT_COLUMNS):
                    raise ValueError
            except ValueError:
                print("Invalid choice.")
                continue

            stat = STAT_COLUMNS[index]
            delta = -1 if lowering else 1
            self.player_data.stats[stat] = self.player_data.stats.get(stat, 0) + delta
            remaining -= 1

        self._sync_max_hp_after_growth()
        print(f"New stats applied. HP: {self.player_data.hp}/{self.player_data.max_hp}")

    def calculate_loot_drop_chance(self):
        """Drop chance scales with Luck, independent of enemy difficulty: 20% baseline,
        +1.5% per Luck point, floored at 5% and capped at 60%."""
        luck = self._effective_stats().get('Luck', 0)
        return max(5, min(60, 20 + luck * 1.5))

    def _roll_for_loot(self):
        """On a successful roll, award one item drawn from the droppable pool, weighted by Rarity"""
        droppable = get_droppable_items()
        if not droppable:
            return

        drop_chance = self.calculate_loot_drop_chance()
        if random.randint(1, 100) > drop_chance:
            return

        names, weights = zip(*droppable)
        item_name = random.choices(names, weights=weights, k=1)[0]
        self.player_data.loot.append(item_name)
        print(f"The enemy dropped {item_name}!")

    def view_stats(self):
        """Display player stats"""
        effective_stats = self._effective_stats()
        print(f"\n=== Player Stats ===")
        print(f"Name: {self.player_data.name}")
        print(f"Role: {self.player_data.role.capitalize()}")
        print(f"Level: {self.player_data.level} ({self.player_data.exp:.1f}% to next level)")
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
        new_max_hp = Player.calculate_hp(self._effective_stats())
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
