"""The start of the game (v1.1.1): the title screen, then who's playing and which adventurer.

    [1] New Player       pick a player name, then make your first adventurer
    [2] My Adventurers   type your player name, then load, delete or create an adventurer
    [3] Exit

Player and adventurer names aren't case sensitive. Empty answers go back a step. Whatever is
chosen ends with input_name() returning (PlayerData, saving_enabled), with the player set active
(players/profiles.py) so saves and unlocks go to them.
"""
import sys

from combat.combat_player import Player
from players import profiles
from players.extract import NewPlayer
from players.save import put_new_player
from util.display import banner, options, table
from util.file_io import delete_player, get_adventurers, get_player
from version import VERSION

YES = ("y", "yes")

WHATS_NEW = """What's new in 1.1.1:
  - Players: your name now holds all your adventurers (and your unlocks), so pick one you'll remember.
  - A fresh coat of paint: colors, bars and tables (install Rich for them: pip install rich).
  - Saves from before are kept aside as players_old.json, so this is a fresh start for everyone."""


class InputName:
	@staticmethod
	def input_name():
		moved = profiles.archive_old_saves()
		print(banner(VERSION))
		print()
		print(WHATS_NEW)
		if moved:
			print("\n(Your old saves were moved to " + " and ".join(path.replace("\\", "/").split("/")[-1] for path in moved)
			      + ". A new journey starts here.)")

		while True:
			print("\nPlease choose an option:\n")
			print(options([("1", "New Player"), ("2", "My Adventurers"), ("3", "Exit")]))
			choice = input("\n> ").strip()
			if choice == "1":
				chosen = new_player()
			elif choice == "2":
				chosen = my_adventurers()
			elif choice == "3":
				print("Farewell, adventurer!")
				sys.exit(0)
			else:
				print("Invalid choice. Please enter 1, 2 or 3.")
				continue
			if chosen:
				return chosen


def new_player():
	"""[1] New Player: a new player name, straight into their first adventurer"""
	print("\nYou chose to create a new user.")
	while True:
		print("To start you off, please input a name to save your adventures behind")
		name = input("Your name (leave empty to go back): ").strip()
		if not name:
			return None
		existing = profiles.find_player(name)
		if existing:
			answer = input("Apparently, this user name is in existence, would you like to load your data instead? "
			               "(y/n/leave empty to go back to main) ").strip().lower()
			if not answer:
				return None
			if answer in YES:
				return adventurer_list(existing)
			print("Then we continue....\n")
			continue
		return first_adventurer(profiles.create_player(name))


def my_adventurers():
	"""[2] My Adventurers: type your player name, then pick an adventurer"""
	while True:
		name = input("\nInput your name to load data from (leave empty to go back): ").strip()
		if not name:
			return None
		stored = profiles.find_player(name)
		if stored:
			chosen = adventurer_list(stored)
			if chosen:
				return chosen
			continue
		answer = input(f'No player data for "{name}" found, would you like to make a New player with that name? (y/n) ')
		if answer.strip().lower() in YES:
			print("Much obliged.")
			chosen = first_adventurer(profiles.create_player(name))
			if chosen:
				return chosen
		else:
			print("Then we continue...")


def first_adventurer(player):
	profiles.set_active(player)
	print(f"\nWelcome {player}, let's create your first adventurer.")
	return create_adventurer(player)


def create_adventurer(player):
	"""Name, then role, then saved. A name this player already uses asks again."""
	profiles.set_active(player)
	while True:
		name = input(f"A new adventure rises in the dawn for {player}, what shall the adventurer name be? "
		             "(leave empty to go back) ").strip()
		if not name:
			return None
		if get_player(name):
			print("This character exists, please use a different name or load it")
			continue
		adventurer = NewPlayer(name)
		put_new_player(adventurer, quiet=True)
		print(f"{adventurer.name} has been saved. Off you go!")
		return adventurer.player_data(), True


def _row(i, pd):
	live = Player(pd)
	where = "in town" if pd.in_town else f"depth {pd.distance}"
	return [f"[{i}]", pd.name, pd.role.capitalize(), pd.level,
	        f"{int(live.current_hp)}/{int(live.max_hp)}", f"{int(live.current_mana)}/{int(live.max_mana)}", where]


def adventurer_list(player):
	"""A player's adventurers: load or delete one, or create a new one"""
	profiles.set_active(player)
	print(f"\nWelcome back {player}.")
	while True:
		adventurers = get_adventurers(player)
		print("Which character shall we touch?\n")
		if adventurers:
			print(table(["#", "Name", "Class", "Level", "HP", "MP", "Where"],
			            [_row(i, pd) for i, pd in enumerate(adventurers, 1)]))
		create = len(adventurers) + 1
		print(options([(str(create), "{Create new adventurer}"), ("0", "Back")], columns=2))
		choice = input("\n> ").strip()
		if choice == "0" or not choice:
			return None
		if choice == str(create):
			chosen = create_adventurer(player)
			if chosen:
				return chosen
			continue
		if not choice.isdigit() or not 1 <= int(choice) <= len(adventurers):
			print("Invalid choice.\n")
			continue
		pd = adventurers[int(choice) - 1]
		action = input(f"{pd.name}: Load or delete (L/D)? (leave empty to go back) ").strip().lower()
		if action == "l":
			print(f"\nWelcome back, {pd.name}! Level {pd.level} {pd.role.capitalize()}.")
			return pd, True
		if action == "d":
			confirm = input(f"Type the adventurer's name to delete {pd.name} for good: ").strip()
			if confirm.lower() == pd.name.lower():
				delete_player(pd.name)
				print(f"{pd.name} has been deleted.\n")
			else:
				print("Deletion cancelled.\n")
		elif action:
			print("Invalid choice.\n")
