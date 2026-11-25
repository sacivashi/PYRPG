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
from items.items_data import rarity_sample, get_item_stats, get_buyable_items, get_droppable_items, is_item_consumable, STAT_COLUMNS
from spells.spells_data import learning_item_spell, can_learn, level_up_spells
from quests.quests_data import get_quests, quest_progress, quest_unlocked, describe_reward, grant_reward, QUEST_TYPES, FAST_TRAVEL
from util.charisma import CHARISMA, charisma_price, price_sway_percent
from util.effects import apply_effects, bonus, describe, tick
from util.events import EventBus


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

    @property
    def events(self):
        """This game's event bus (util/events.py), built on first use with the game's own listeners:
        quests count kills, depth and fast travel from it, and boons & curses wear off on it."""
        if getattr(self, "_events", None) is None:
            self._events = EventBus()
            self._events.on("victory", lambda enemy, size: self.quest_event("defeat", enemy, size))
            self._events.on("explore", lambda distance: self.quest_event("reach", distance))
            self._events.on("fast_travel", lambda depth: self.quest_event("use", FAST_TRAVEL))
            for event in ("explore", "rest", "rested", "town_rest", "victory"):
                self._events.on(event, lambda event=event, **_: self._tick_effects(event))
        return self._events

    def _tick_effects(self, event):
        """Count one `event` against the active boons & curses, and say which ones just wore off"""
        ended = tick(self.player_data.effects, event)
        for effect in ended:
            print(f"{effect['name']} wears off.")
        if ended:
            self._refresh_max_hp()

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
        self.events.emit("explore", distance=self.player_data.distance)
        if not self.passive_encounter():
            self.enter_combat()

    def passive_encounter(self):
        """25% of explores: something from encounters.csv instead of a fight (a chest, the Cook, an
        adventure...). Returns True if one happened."""
        from adventures.encounters import roll_wild_encounter, run_encounter
        row = roll_wild_encounter(self)
        if row is None:
            return False
        run_encounter(self, row)
        return True

    def town_encounter(self):
        """On the way back into town: the town rows of encounters.csv (Halt!). Returns True if one happened."""
        from adventures.encounters import roll_town_encounter, run_encounter
        row = roll_town_encounter(self)
        if row is None:
            return False
        run_encounter(self, row)
        return True

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
        self.events.emit("fast_travel", depth=depth)
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
            if not self.town_encounter():
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
        self.events.emit("town_rest")  # lifts curses first, so the heal is to the uncursed max
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
            sway = price_sway_percent(self._charisma())
            if sway:
                print(f"(Charisma: prices {sway}% {'lower' if self._charisma() > 0 else 'higher'} for you)")
            for i, (name, price) in enumerate(stock, 1):
                if (i - 1) in sold_out:
                    print(f"  [{i}] {name} - SOLD OUT")
                else:
                    print(f"  [{i}] {name} - {self._shop_price(price, has_voucher)} gold")
            print(f"  [5] Reroll stock - {reroll_cost} gold")
            for slot, (name, price) in enumerate(self.ALWAYS_STOCKED, 6):
                print(f"  [{slot}] {name} - {self._shop_price(price, has_voucher)} gold (always in stock)")
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
        """Charge for one item (Charisma sway, then the Voucher discount, which gets used up).
        Returns True if bought."""
        final_price = self._shop_price(price, has_voucher)
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

    def _shop_price(self, price, has_voucher=False):
        """What the shop actually charges: swayed by your Charisma, then the Voucher on top"""
        return self._apply_voucher_discount(charisma_price(price, self._charisma()), has_voucher)

    def _charisma(self):
        return self._effective_stats().get(CHARISMA, 0)

    def _roll_shop_stock(self):
        """Pick the shop's stock from the buyable items, weighted by Rarity (rarer = shows up less)"""
        return rarity_sample(get_buyable_items(), self.SHOP_STOCK_SIZE)

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
        print(f"  Price: {self._shop_price(price)} gold")
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
        return self.fight(enemy_name, group_size)

    def fight(self, enemy_name, group_size=1, surprise=False, scaling=0, on_victory=None):
        """Run one fight and settle it: rewards on a win, death penalties on a loss. Shared by
        random encounters and adventures, so a fight pays out the same wherever it happens.
        `surprise`: every enemy acts first. `scaling`: flat bonus to the enemy's positive stats
        (Mimics, thief merchants). `on_victory`: extra payout, run after the usual rewards."""
        # Auto-save before risky combat
        print("💾 Auto-saving before combat...")
        self.auto_save_player_state()

        extras = {k: v for k, v in (("surprise", surprise), ("scaling", scaling)) if v}
        result, current_hp, current_mana = start_combat(self.player_data, enemy_name, group_size, **extras)
        self.player_data.hp = current_hp
        self.player_data.mana = current_mana

        if result == "victory":
            # Rewards are per-enemy, summed independently rather than one roll * group_size,
            # so a group's payout has the same variance as fighting each member separately.
            gold_reward = sum(self.calculate_gold_reward() for _ in range(group_size))
            gold_reward = int(bonus(self.player_data.effects, "gold", gold_reward))
            self.player_data.gold += gold_reward
            print(f"You gained {gold_reward} gold!")

            exp_reward = sum(self.calculate_exp_reward(enemy_name) for _ in range(group_size))
            exp_reward = bonus(self.player_data.effects, "EXP", exp_reward)
            self.player_data.exp += exp_reward
            print(f"You gained {exp_reward:.1f}% EXP!")
            self._process_level_ups()

            for _ in range(group_size):
                self._roll_for_loot()

            self.events.emit("victory", enemy=enemy_name, size=group_size)
            self._sleight_of_stats_progress()
            if on_victory:
                on_victory()
        elif result == "defeat":
            self._apply_death_penalties()
            self._handle_defeat_respawn()
        # "fled": no rewards, no penalty — nothing to do beyond the HP sync already above

        input("\nPress Enter to continue...")
        return result

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
    NUTS_HEAL = 5

    def use_item_outside_combat(self, item_name):
        """Potions and spell-learning items work outside combat. Returns True if the item was used up."""
        key = item_name.lower()
        if key == "health potion":
            self.player_data.hp = min(self.player_data.max_hp, self.player_data.hp + self.POTION_AMOUNT)
            print(f"You drink a Health potion. HP: {self.player_data.hp}/{self.player_data.max_hp}")
        elif key == "mana potion":
            self.player_data.mana = min(self._max_mana(), self._current_mana() + self.POTION_AMOUNT)
            print(f"You drink a Mana potion. Mana: {self.player_data.mana}/{self._max_mana()}")
        elif key == "nuts":
            self.player_data.hp = min(self.player_data.max_hp, self.player_data.hp + self.NUTS_HEAL)
            print(f"You munch some Nuts. HP: {self.player_data.hp}/{self.player_data.max_hp}")
        elif key == "prayer card":
            from adventures.encounters import prayer_card
            prayer_card(self)
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

    def quest_event(self, quest_type, value, amount=1):
        """Report something that happened — a won fight ("defeat", enemy name, group size), an action
        ("use", FAST_TRAVEL), a depth ("reach", distance) — and count it toward every accepted,
        unfinished quest of that type whose target it matches (QUEST_TYPES in quests/quests_data.py).
        Quests you haven't accepted yet don't count anything."""
        matches = QUEST_TYPES[quest_type]
        flags = self.player_data.quest_flags
        for quest_id, quest in get_quests().items():
            if (quest["type"] == quest_type and quest_id in self.player_data.accepted_quests
                    and quest_id not in self.player_data.completed_quests
                    and matches(quest["target"], value)):
                flags[quest_id] = min(quest["amount"], quest_progress(quest_id, quest, flags) + amount)

    def _quest_status(self, quest_id, quest):
        """"completed", "new" (not accepted yet), "in progress" or "ready" (to claim). Spend quests
        have nothing to do out in the world, so you make their choice the moment you open them."""
        if quest_id in self.player_data.completed_quests:
            return "completed"
        if quest["type"] == "spend":
            return "choose"
        if quest_id not in self.player_data.accepted_quests:
            return "new"
        if quest_progress(quest_id, quest, self.player_data.quest_flags) >= quest["amount"]:
            return "ready"
        return "in progress"

    def _quest_status_label(self, quest_id, quest):
        status = self._quest_status(quest_id, quest)
        if status == "in progress":
            return f"In progress ({quest_progress(quest_id, quest, self.player_data.quest_flags)}/{quest['amount']})"
        return {"completed": "Completed", "choose": "New", "new": "New", "ready": "Ready to claim!"}[status]

    def _visible_quests(self):
        """The board's quests, minus quest-chain ones whose earlier quest isn't done yet"""
        return [(quest_id, quest) for quest_id, quest in get_quests().items()
                if quest_unlocked(quest_id, self.player_data.completed_quests)]

    def quest_board(self):
        """Town quest board: pick a quest to read it, accept it, fight for it or claim it"""
        while True:
            quests = self._visible_quests()
            print("\n=== Quest Board ===")
            print(f"Gold: {self.player_data.gold}")
            for i, (quest_id, quest) in enumerate(quests, 1):
                print(f"  [{i}] {quest['title']} - {self._quest_status_label(quest_id, quest)}")
            print("  [0] Leave")

            choice = input("\nChoose a quest (0 or Enter to leave): ").strip()
            if choice in ("0", ""):
                return
            try:
                index = int(choice) - 1
                if index < 0 or index >= len(quests):
                    raise ValueError
            except ValueError:
                print("Invalid choice.")
                continue
            self._open_quest(*quests[index])

    def _open_quest(self, quest_id, quest):
        """One quest's page: what it says and whatever you can do with it right now"""
        print(f"\n--- {quest['title']} ---")
        print(quest["description"] or "...")
        status = self._quest_status(quest_id, quest)

        if status == "completed":
            made = self.player_data.quest_choices.get(quest_id)
            print(f"Completed{f' (you chose: {made})' if made else ''}.")
            input("\nPress Enter to continue...")
        elif status == "new":
            self._offer_quest(quest_id, quest)
        elif status == "in progress":
            print(f"{self._quest_status_label(quest_id, quest)}.")
            if quest["spawn"]:
                name, count = quest["spawn"]
                if input(f"[1] Fight ({count} {name})  [0] Back: ").strip() == "1":
                    self._quest_fight(quest)
            else:
                input("\nPress Enter to continue...")
        else:
            self._complete_quest(quest_id, quest)

    def _offer_quest(self, quest_id, quest):
        """Accept a quest, or leave it for later. Quests with a spawn start their fight right away."""
        options = quest["options"]
        if len(options) > 1:
            print("Reward: depends on what you choose...")
        elif describe_reward(options[0]["reward"]):
            print(f"Reward: {describe_reward(options[0]['reward'])}")
        if input("[1] Accept  [0] Not now: ").strip() != "1":
            return
        self.player_data.accepted_quests.append(quest_id)
        print("Quest accepted!")
        if quest["spawn"]:
            self._quest_fight(quest)
        else:
            input("\nPress Enter to continue...")

    def _quest_fight(self, quest):
        """Fight a quest's own enemies, right here in town"""
        name, count = quest["spawn"]
        stats = get_enemy_stats(name)
        name = stats["Name"] if stats else name
        if count > 1:
            print(f"\n{count} {name}s step up. Fight!")
        else:
            print(f"\nA {name} steps up. Fight!")
        self.fight(name, count)

    def _option_label(self, option):
        """'Give (20 gold)', 'Accept (costs 55 gold, Dice machine)', 'Claim (30 gold)', 'Decline'"""
        details = [f"costs {option['cost']} gold" if option["cost"] else None, describe_reward(option["reward"])]
        details = ", ".join(d for d in details if d)
        return f"{option['label'] or 'Claim'}{f' ({details})' if details else ''}"

    def _complete_quest(self, quest_id, quest):
        """Claim a finished quest, or make a choice quest's choice. Every choice completes the quest:
        pay its cost (spend quests), get its reward, and take its Charisma change."""
        options = quest["options"]
        menu = "  ".join(f"[{i}] {self._option_label(option)}" for i, option in enumerate(options, 1))
        choice = input(f"{menu}  [0] Not now: ").strip()
        if not choice.isdigit() or not 1 <= int(choice) <= len(options):
            return
        option = options[int(choice) - 1]
        if option["cost"] > self.player_data.gold:
            print(f"You need {option['cost']} gold for that (you have {self.player_data.gold}).")
            input("\nPress Enter to continue...")
            return

        self.player_data.gold -= option["cost"]
        grant_reward(self.player_data, option["reward"])
        if option["charisma"]:
            stats = self.player_data.stats
            stats[CHARISMA] = stats.get(CHARISMA, 0) + option["charisma"]
        if quest_id not in self.player_data.accepted_quests:
            self.player_data.accepted_quests.append(quest_id)
        if option["label"]:
            self.player_data.quest_choices[quest_id] = option["label"]
        self.player_data.completed_quests.append(quest_id)

        reward = describe_reward(option["reward"])
        print(f"Quest complete!{f' Reward: {reward}.' if reward else ''}")
        if option["charisma"]:
            print(f"Charisma {option['charisma']:+d} (now {self.player_data.stats[CHARISMA]}).")
        input("\nPress Enter to continue...")

    def calculate_rest_chance(self):
        """min(60, max(30, Luck + 15))% for Luck >= 0; max(15, 25 - abs(Luck) * 0.48)% for -Luck"""
        luck = self._effective_stats().get('Luck', 0)
        if luck < 0:
            chance = round(max(15, 25 - abs(luck) * 0.48), 1)
        else:
            chance = min(60, max(30, luck + 15))
        return bonus(self.player_data.effects, "rest_chance", chance)  # Of resting: +15

    def _effective_stats(self):
        """Base stats with the equipped item's deltas applied — what the character actually has
        right now. Everything outside combat that reads a stat (rest odds, rewards, encounters,
        max HP) goes through this so gear counts everywhere, not just in fights."""
        return apply_effects(self._gear_stats(), self.player_data.effects)

    def _gear_stats(self):
        """Base stats + gear, without boons & curses"""
        return Player.apply_equipment(self.player_data.stats, self.player_data.equipped)

    def _max_hp(self):
        return Player.max_hp_with_effects(self._effective_stats(), self.player_data.effects)

    def _unequip_consumable(self):
        """Consumables can't be worn — a save from before the Dice machine became one gets it unequipped"""
        if self.player_data.equipped and is_item_consumable(self.player_data.equipped):
            print(f"Your {self.player_data.equipped} is a usable item now, so it has been unequipped.")
            self.player_data.equipped = None
            self._apply_equipment_hp_change()

    def _player_power(self):
        """Sum of the player's absolute stats with gear applied — the yardstick encounters are matched
        against. Charisma doesn't count: it never makes you stronger in a fight. Neither do boons &
        curses: a crippled character still meets what their gear says they can handle."""
        return sum(abs(int(v)) for k, v in self._gear_stats().items() if k != CHARISMA)

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
        new_max_hp = self._max_hp()
        self.player_data.hp = min(self.player_data.hp, new_max_hp)
        self.player_data.max_hp = new_max_hp

    REST_RESTORATION = 0.30  # of max HP & mana per successful rest out there

    def rest(self):
        """Attempt to rest: Luck-based odds to succeed and recover 30% max HP and mana, otherwise ambushed into combat"""
        success_chance = self.calculate_rest_chance()
        restoration = bonus(self.player_data.effects, "rest_restoration", self.REST_RESTORATION)
        roll = random.randint(1, 100)
        self.events.emit("rest")

        print(f"\nYou attempt to rest... ({success_chance:g}% chance of success)")

        if roll <= success_chance:
            heal_amount = round(self.player_data.max_hp * restoration)
            self.player_data.hp = min(self.player_data.max_hp, self.player_data.hp + heal_amount)
            max_mana = self._max_mana()
            mana_amount = round(max_mana * restoration)
            self.player_data.mana = min(max_mana, self._current_mana() + mana_amount)
            print(f"You rest peacefully and recover {heal_amount} HP and {mana_amount} mana.")
            print(f"HP: {self.player_data.hp}/{self.player_data.max_hp}")
            print(f"Mana: {self.player_data.mana}/{max_mana}")
            self.events.emit("rested")
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

    DROP_STACK_SIZES = {"nuts": 4}  # items that drop as a stack instead of one copy

    CHEST_GOLD = (5, 13)

    def open_chest(self):
        """A real treasure chest: 5 ~ 13 gold and a loot roll. Whether a chest is a Mimic is
        decided before this — by the encounter roll — so anything that calls this is safe."""
        gold = random.randint(*self.CHEST_GOLD)
        self.player_data.gold += gold
        print(f"You open the chest and find {gold} gold!")
        self._roll_for_loot(source="The chest held")

    def _roll_for_loot(self, source="The enemy dropped"):
        """On a successful roll, award one item drawn from the droppable pool, weighted by Rarity"""
        droppable = get_droppable_items()
        if not droppable:
            return

        drop_chance = self.calculate_loot_drop_chance()
        if random.randint(1, 100) > drop_chance:
            return

        names, weights = zip(*droppable)
        item_name = random.choices(names, weights=weights, k=1)[0]
        amount = self.DROP_STACK_SIZES.get(item_name.lower(), 1)
        self.player_data.loot.extend([item_name] * amount)
        print(f"{source} {item_name}{f' (x{amount})' if amount > 1 else ''}!")

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
        if self.player_data.effects:
            print("Boons & curses:")
            for effect in self.player_data.effects:
                print(f"  {describe(effect)}")

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
        new_max_hp = self._max_hp()
        self.player_data.hp = min(self.player_data.hp, new_max_hp)
        self.player_data.max_hp = new_max_hp
        self.player_data.mana = self._current_mana()

    def _refresh_max_hp(self):
        """A boon or curse started or ended: same as a gear change (the cap moves, current only clamps)"""
        self._apply_equipment_hp_change()

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
