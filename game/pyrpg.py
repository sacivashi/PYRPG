import random
import sys
import os

# Add the project root to Python path so we can import top-level modules
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from players.input_name import InputName
from combat.combat import start_combat, roll_group_size
from enemies.enemies_data import get_encounter_enemy, get_enemy_difficulty, get_enemy_stats, DEATH
from players.save import put_new_player
from combat.combat_player import Player
from items.items_data import get_item_stats, get_buyable_items, get_droppable_items, is_item_consumable, STAT_COLUMNS
from spells.spells_data import learning_item_spell, can_learn, level_up_spells
from quests.quests_data import get_quests, quest_progress, describe_reward, FAST_TRAVEL


class PYRPG:
    def __init__(self):
        # Initialize player and this session's save consent (asked once, inside InputName.input_name())
        self.player_data, self.saving_enabled = InputName.input_name()

        # Older saves may have an item equipped that's now a consumable (the Dice machine)
        self._unequip_consumable()
        # Characters already past a level-up spell's level (saves from before it existed) still get it
        self._learn_level_up_spells()

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
        print("[2] Fast Travel")
        print("[3] Rest")
        print("[4] Shop")
        print("[5] Quest Board")
        print("[6] View Stats")
        print("[7] Manage Loot")
        print("[8] Save Game")
        print("[9] Exit Game")

        choice = input("\nChoose an option: ").strip()

        if choice == "1":
            self.travel_outside()
        elif choice == "2":
            self.fast_travel()
        elif choice == "3":
            self.full_rest()
        elif choice == "4":
            self.shop()
        elif choice == "5":
            self.quest_board()
        elif choice == "6":
            self.view_stats()
        elif choice == "7":
            self.manage_loot()
        elif choice == "8":
            self.save_game()
        elif choice == "9":
            return "exit"
        else:
            print("Invalid choice. Please enter a number between 1 and 9.")

    def wild_menu(self):
        """Menu shown while out in the wild"""
        print(f"\n=== Out in the Wild ===")
        print(f"Distance from town: {self.player_data.distance} (deepest reached: {self.player_data.depth_reached})")
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
        self.player_data.depth_reached = max(self.player_data.depth_reached, self.player_data.distance)
        self.enter_combat()

    FREE_FAST_TRAVEL = "free_fast_travel"

    @staticmethod
    def fast_travel_cost(depth):
        """int(5 * depth * 0.5) gold — deeper jumps cost more"""
        return int(5 * depth * 0.5)

    def fast_travel(self):
        """Pay gold to jump straight to any depth up to the deepest one ever reached"""
        reached = self.player_data.depth_reached
        if reached < 1:
            print("\nYou haven't ventured out yet — there's nowhere to fast travel to.")
            input("\nPress Enter to continue...")
            return

        print(f"\n=== Fast Travel ===")
        print(f"Gold: {self.player_data.gold}")
        if self.FREE_FAST_TRAVEL in self.player_data.perks:
            print(f"Deepest depth reached: {reached} (your next trip is free!)")
        else:
            print(f"Deepest depth reached: {reached} "
                  f"(depth 1 costs {self.fast_travel_cost(1)} gold, depth {reached} costs {self.fast_travel_cost(reached)})")
        choice = input(f"Travel to which depth? (1-{reached}, 0 to cancel): ").strip()

        try:
            depth = int(choice)
        except ValueError:
            depth = -1
        if depth == 0:
            return
        if depth < 1 or depth > reached:
            print("Invalid depth.")
            input("\nPress Enter to continue...")
            return

        free_trip = self.FREE_FAST_TRAVEL in self.player_data.perks
        cost = 0 if free_trip else self.fast_travel_cost(depth)
        if self.player_data.gold < cost:
            print(f"Traveling to depth {depth} costs {cost} gold, but you only have {self.player_data.gold}.")
            input("\nPress Enter to continue...")
            return

        self.player_data.gold -= cost
        self.player_data.in_town = False
        self.player_data.distance = depth
        self.player_data.failed_attempts = 0
        if free_trip:
            self.player_data.perks.remove(self.FREE_FAST_TRAVEL)
            print(f"Your free trip takes you to depth {depth} at no cost!")
        else:
            print(f"You pay {cost} gold and arrive at depth {depth}.")
        self._record_quest_use(FAST_TRAVEL)
        input("\nPress Enter to continue...")

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
    DEATH_GOLD_LOSS = 0.15
    DEATH_ITEM_LOSS_CHANCE = 25  # % chance one random owned item (equipped or not) is lost
    DEATH_EXP_LOSS = 0.20  # of current progress toward the next level — never drops a level
    DEATH_HP_RESTORE = 0.50
    DEATH_MANA_RESTORE = 0.30

    def _apply_death_penalties(self):
        """Gold, item and EXP losses, then resurrect at partial HP/mana. The item goes first so
        HP and mana are restored against the post-loss max — losing gear can lower both."""
        gold_lost = int(self.player_data.gold * self.DEATH_GOLD_LOSS)
        self.player_data.gold -= gold_lost
        print(f"You lost {gold_lost} gold.")

        if self.player_data.loot and random.randint(1, 100) <= self.DEATH_ITEM_LOSS_CHANCE:
            lost_item = random.choice(self.player_data.loot)
            self.player_data.loot.remove(lost_item)
            print(f"Your {lost_item} was lost!")
            if lost_item == self.player_data.equipped and lost_item not in self.player_data.loot:
                self.player_data.equipped = None
                self._apply_equipment_hp_change()

        exp_lost = self.player_data.exp * self.DEATH_EXP_LOSS
        self.player_data.exp -= exp_lost
        print(f"You lost {exp_lost:.1f}% EXP progress.")

        self.player_data.hp = max(1, int(self.player_data.max_hp * self.DEATH_HP_RESTORE))
        self.player_data.mana = int(self._max_mana() * self.DEATH_MANA_RESTORE)

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
        self.player_data.mana = self._max_mana()
        print(f"\nYou pay {self.REST_COST} gold and rest fully, recovering all your HP and mana.")
        print(f"HP: {self.player_data.hp}/{self.player_data.max_hp}")
        print(f"Mana: {self.player_data.mana}/{self._max_mana()}")
        input("\nPress Enter to continue...")

    SHOP_STOCK_SIZE = 4
    REROLL_BASE_COST = 5
    REROLL_COST_STEP = 5
    VOUCHER_DISCOUNT = 0.15
    # Always on the shelf, never sold out, outside the rotating stock (menu slots 6 and 7)
    ALWAYS_STOCKED = [("Health potion", 15), ("Mana potion", 15)]

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
            for slot, (name, price) in enumerate(self.ALWAYS_STOCKED, 6):
                print(f"  [{slot}] {name} - {self._apply_voucher_discount(price, has_voucher)} gold (always in stock)")
            print("  [0] Leave shop")

            choice = input("\nChoose an item to buy, 'c' + number to check its stats (e.g. c1), 5 to reroll, 6/7 for potions, or 0 to leave: ").strip()

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

            always_slots = {str(slot): entry for slot, entry in enumerate(self.ALWAYS_STOCKED, 6)}
            if choice in always_slots:
                self._buy(*always_slots[choice], has_voucher)
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

            if self._buy(*stock[index], has_voucher):
                sold_out.add(index)

    def _buy(self, item_name, price, has_voucher):
        """Charge for one item (Voucher discount applied and used up). Returns True if bought."""
        final_price = self._apply_voucher_discount(price, has_voucher)
        if self.player_data.gold < final_price:
            print("You don't have enough gold.")
            input("\nPress Enter to continue...")
            return False

        self.player_data.gold -= final_price
        self.player_data.loot.append(item_name)
        print(f"Bought {item_name} for {final_price} gold.")
        if has_voucher:
            self.player_data.loot.remove("Voucher")
            print("Your Voucher is used up.")
        input("\nPress Enter to continue...")
        return True

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
        depth = self.player_data.distance
        enemy_name = get_encounter_enemy(self._player_power(), depth)
        group_size = 1 if enemy_name == DEATH else roll_group_size(depth)
        if enemy_name == DEATH:
            print("\nThe air goes cold. Death has come for you...")
        elif group_size > 1:
            print(f"\nA group of {group_size} {enemy_name}s appears!")
        else:
            print(f"\nA wild {enemy_name} appears!")

        # Auto-save before risky combat
        print("💾 Auto-saving before combat...")
        self.auto_save_player_state()

        result, current_hp, current_mana = start_combat(self.player_data, enemy_name, group_size)
        self.player_data.hp = current_hp
        self.player_data.mana = current_mana

        if result == "victory":
            # Rewards are per-enemy, summed independently rather than one roll * group_size,
            # so a group's payout has the same variance as fighting each member separately.
            gold_reward = sum(self.calculate_gold_reward() for _ in range(group_size))
            self.player_data.gold += gold_reward
            print(f"You gained {gold_reward} gold!")

            exp_reward = sum(self.calculate_exp_reward(enemy_name) for _ in range(group_size))
            self.player_data.exp += exp_reward
            print(f"You gained {exp_reward:.1f}% EXP!")
            self._process_level_ups()

            for _ in range(group_size):
                self._roll_for_loot()

            self._update_quest_progress(enemy_name, group_size)
            self._sleight_of_stats_progress()
        elif result == "defeat":
            self._apply_death_penalties()
            self._handle_defeat_respawn()
        # "fled": no rewards, no penalty — nothing to do beyond the HP sync already above

        input("\nPress Enter to continue...")

    SLEIGHT_OF_STATS = "sleight of stats"
    SLEIGHT_WINS_PER_POINT = 3
    SLEIGHT_MAX_PER_STAT = 10

    def _sleight_of_stats_progress(self):
        """Sleight of stats: every 3 wins while it's worn, one random stat permanently gains +1,
        up to +10 per stat over the item's lifetime. Progress lives in item_state."""
        if (self.player_data.equipped or "").lower() != self.SLEIGHT_OF_STATS:
            return
        state = self.player_data.item_state.setdefault(self.SLEIGHT_OF_STATS, {"wins": 0, "gains": {}})
        state["wins"] += 1
        if state["wins"] < self.SLEIGHT_WINS_PER_POINT:
            return
        state["wins"] = 0
        open_stats = [s for s in STAT_COLUMNS if state["gains"].get(s, 0) < self.SLEIGHT_MAX_PER_STAT]
        if not open_stats:
            return
        stat = random.choice(open_stats)
        state["gains"][stat] = state["gains"].get(stat, 0) + 1
        self.player_data.stats[stat] = self.player_data.stats.get(stat, 0) + 1
        print(f"Sleight of stats shuffles fate in your favour: {stat} +1!")
        self._sync_max_hp_after_growth()

    POTION_AMOUNT = 20

    def use_item_outside_combat(self, item_name):
        """Potions and spell-learning items work outside combat. Returns True if the item was used up."""
        key = item_name.lower()
        if key == "health potion":
            self.player_data.hp = min(self.player_data.max_hp, self.player_data.hp + self.POTION_AMOUNT)
            print(f"You drink a Health potion. HP: {self.player_data.hp}/{self.player_data.max_hp}")
        elif key == "mana potion":
            self.player_data.mana = min(self._max_mana(), self._current_mana() + self.POTION_AMOUNT)
            print(f"You drink a Mana potion. Mana: {self.player_data.mana}/{self._max_mana()}")
        elif learning_item_spell(item_name):
            spell = learning_item_spell(item_name)
            if spell in self.player_data.known_spells:
                print(f"You already know {spell}.")
                return False
            if not can_learn(spell, self._effective_stats().get('Magic', 0)):
                print(f"{spell} is a cursed spell — only those with negative Magic can learn it.")
                return False
            self.player_data.known_spells.append(spell)
            print(f"You study the {item_name} and learn {spell}!")
        else:
            print(f"{item_name} can only be used in combat.")
            return False
        self.player_data.loot.remove(item_name)
        return True

    def _update_quest_progress(self, enemy_name, defeated=1):
        """Called after every victory — counts the fight toward every unfinished "defeat" quest
        (data/quests.csv) whose target it was. A group counts every enemy in it."""
        self._advance_quests("defeat", enemy_name, defeated)

    def _record_quest_use(self, action):
        """Called when the player does something a "use" quest can ask for (e.g. FAST_TRAVEL)"""
        self._advance_quests("use", action, 1)

    def _advance_quests(self, quest_type, target, amount):
        flags = self.player_data.quest_flags
        for quest_id, quest in get_quests().items():
            if quest_id in self.player_data.completed_quests or quest["type"] != quest_type:
                continue
            if target.lower() == quest["target"].lower():
                flags[quest_id] = min(quest["amount"], quest_progress(quest_id, quest, flags) + amount)

    def quest_board(self):
        """Town quest board — lists every quest, lets you turn in ones that are ready"""
        print("\n=== Quest Board ===")
        for quest_id, quest in get_quests().items():
            print(f"\n{quest['title']}: {quest['description']}")
            progress = quest_progress(quest_id, quest, self.player_data.quest_flags)

            if quest_id in self.player_data.completed_quests:
                print("  Status: Completed.")
            elif progress >= quest["amount"]:
                reward = quest["reward"]
                choice = input(f"  Ready to turn in for {describe_reward(reward)}! Claim it now? (yes/no): ").strip().lower()
                if choice in ("y", "yes"):
                    if isinstance(reward, int):
                        self.player_data.gold += reward
                    else:
                        self.player_data.perks.append(reward)
                    self.player_data.completed_quests.append(quest_id)
                    print(f"  Quest complete! Reward: {describe_reward(reward)}.")
            else:
                print(f"  Status: In progress ({progress}/{quest['amount']}).")

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

    def _unequip_consumable(self):
        """Consumables can't be worn — a save from before the Dice machine became one gets it unequipped"""
        if self.player_data.equipped and is_item_consumable(self.player_data.equipped):
            print(f"Your {self.player_data.equipped} is a usable item now, so it has been unequipped.")
            self.player_data.equipped = None
            self._apply_equipment_hp_change()

    def _player_power(self):
        """Sum of the player's absolute stats with gear applied — the yardstick encounters are matched against"""
        return sum(abs(int(v)) for v in self._effective_stats().values())

    def _max_mana(self):
        """Max mana from gear-adjusted stats — never stored, always derived, like max HP in combat"""
        return Player.calculate_mana(self._effective_stats())

    def _current_mana(self):
        """Saved mana capped at the current max; None (new character / pre-mana save) means full"""
        max_mana = self._max_mana()
        return max_mana if self.player_data.mana is None else min(self.player_data.mana, max_mana)

    def _sync_max_hp_after_growth(self):
        """Recompute max HP (gear included) after a permanent stat gain. Raises the cap only — no free
        heal, same as mana; clamps in case the stat change lowered max HP."""
        new_max_hp = Player.calculate_hp(self._effective_stats())
        self.player_data.hp = min(self.player_data.hp, new_max_hp)
        self.player_data.max_hp = new_max_hp

    def rest(self):
        """Attempt to rest: Luck-based odds to succeed and recover 30% max HP and mana, otherwise ambushed into combat"""
        success_chance = self.calculate_rest_chance()
        roll = random.randint(1, 100)

        print(f"\nYou attempt to rest... ({success_chance:g}% chance of success)")

        if roll <= success_chance:
            heal_amount = round(self.player_data.max_hp * 0.30)
            self.player_data.hp = min(self.player_data.max_hp, self.player_data.hp + heal_amount)
            max_mana = self._max_mana()
            mana_amount = round(max_mana * 0.30)
            self.player_data.mana = min(max_mana, self._current_mana() + mana_amount)
            print(f"You rest peacefully and recover {heal_amount} HP and {mana_amount} mana.")
            print(f"HP: {self.player_data.hp}/{self.player_data.max_hp}")
            print(f"Mana: {self.player_data.mana}/{max_mana}")
            input("\nPress Enter to continue...")
        else:
            print("Your rest is interrupted!")
            self.enter_combat()

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
            self._learn_level_up_spells()

    def _learn_level_up_spells(self):
        """Learn every LEVEL_UP_SPELLS entry the role has reached and can learn. Safe to call any
        time — it's also run on load, so characters already past the level still get theirs."""
        magic = self._effective_stats().get('Magic', 0)
        for spell in level_up_spells(self.player_data.role, self.player_data.level):
            if spell not in self.player_data.known_spells and can_learn(spell, magic):
                self.player_data.known_spells.append(spell)
                print(f"You learned {spell}!")

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
        print(f"Mana: {self._current_mana()}/{self._max_mana()}")
        print(f"Gold: {self.player_data.gold}")
        print(f"Loot: {', '.join(self._stack_label(n, c) for n, c in self._stacked_loot()) or 'None'}")
        print(f"Equipped: {self.player_data.equipped or 'Nothing'}")
        print(f"Spells & Abilities: {', '.join(self.player_data.known_spells) or 'None'}")
        print("Stats:")
        for stat, value in effective_stats.items():
            print(f"  {stat}: {value}")

        input("\nPress Enter to continue...")

    def manage_loot(self):
        """Equip or unequip an item from loot, or use a consumable that works outside combat"""
        while True:
            print(f"\n=== Loot ===")
            print(f"Gold: {self.player_data.gold}")
            print(f"Equipped: {self.player_data.equipped or 'Nothing'}")

            if not self.player_data.loot:
                print("You have no loot.")
                input("\nPress Enter to continue...")
                return

            stacks = self._stacked_loot()
            print("Inventory:")
            for i, (item_name, count) in enumerate(stacks, 1):
                print(f"  [{i}] {self._stack_label(item_name, count)}")
            if self.player_data.equipped:
                print(f"  [u] Unequip {self.player_data.equipped}")
            print("  [0] Back")

            choice = input("\nChoose an item to equip or use, 'c' + number to check its stats (e.g. c1), "
                           f"{'u to unequip, ' if self.player_data.equipped else ''}or 0 to go back: ").strip()

            if choice == "0":
                return

            if choice.lower() == "u" and self.player_data.equipped:
                print(f"Unequipped {self.player_data.equipped}.")
                self.player_data.equipped = None
                self._apply_equipment_hp_change()
                input("\nPress Enter to continue...")
                return

            if choice.lower().startswith("c"):
                self._check_loot_stats(choice[1:].strip())
                continue

            try:
                index = int(choice) - 1
                if index < 0 or index >= len(stacks):
                    raise ValueError
            except ValueError:
                print("Invalid choice.")
                input("\nPress Enter to continue...")
                continue

            item_name = stacks[index][0]
            if is_item_consumable(item_name):
                self.use_item_outside_combat(item_name)
                input("\nPress Enter to continue...")
                continue

            self.player_data.equipped = item_name
            print(f"Equipped {self.player_data.equipped}.")
            self._apply_equipment_hp_change()
            input("\nPress Enter to continue...")
            return

    def _stacked_loot(self):
        """[(item_name, count), ...] — duplicates grouped, in first-picked-up order. Loot itself stays
        a flat list (one entry per copy), so saves and everything that adds/removes items are unchanged."""
        counts = {}
        for item_name in self.player_data.loot:
            counts[item_name] = counts.get(item_name, 0) + 1
        return list(counts.items())

    def _stack_label(self, item_name, count):
        label = f"{item_name} (x{count})" if count > 1 else item_name
        return f"{label} [equipped]" if item_name == self.player_data.equipped else label

    def _check_loot_stats(self, index_str):
        """Show the stat deltas for one item in loot, without equipping it"""
        stacks = self._stacked_loot()
        try:
            index = int(index_str) - 1
            if index < 0 or index >= len(stacks):
                raise ValueError
        except ValueError:
            print("Invalid item number.")
            input("\nPress Enter to continue...")
            return

        self._print_item_stats(stacks[index][0])
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
        """Recompute max HP and mana after equipping/unequipping. Clamp only — no free heal or refill from gear."""
        new_max_hp = Player.calculate_hp(self._effective_stats())
        self.player_data.hp = min(self.player_data.hp, new_max_hp)
        self.player_data.max_hp = new_max_hp
        self.player_data.mana = self._current_mana()

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
