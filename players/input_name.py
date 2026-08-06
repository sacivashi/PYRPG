import time

from util.file_io import get_player, delete_player
from players.extract import NewPlayer
from players.save import put_new_player

player = None


class InputName:
	@staticmethod
	def input_name():
		global player

		while True:
			your_name = input(
				"""Welcome to PyRPG.
	This project is a text based RPG game.
	Please look at patch notes files to see new patches or features.\n
	To start you off, please input your name: """).strip()

			player_info = get_player(your_name)
			if player_info is not None:
				while True:
					choice = input(f"A save for '{player_info.name}' already exists. [1] Load [2] Delete [3] Cancel: ").strip()
					if choice == "1":
						print(f"Welcome back, {player_info.name.capitalize()}!")
						print(f"Role: {player_info.role.capitalize()}, Level: {player_info.level}")
						print("Stats:", player_info.stats)
						return player_info
					elif choice == "2":
						confirm = input(f"Are you sure you want to delete '{player_info.name}'s save? This cannot be undone. (yes/no) ").strip().lower()
						if confirm in ("y", "yes"):
							delete_player(your_name)
							print(f"'{player_info.name}'s save has been deleted.\n")
							time.sleep(0.4)
							break  # back to name prompt
						else:
							print("Deletion cancelled.\n")
					elif choice == "3":
						print()
						break  # back to name prompt
					else:
						print("Invalid choice. Please enter 1, 2, or 3.")
			else:
				player = NewPlayer(your_name)
				playersave = input(f"{your_name.title()}, would you like to be added to the save files? (yes/no) ")
				if playersave in ('yes', 'y'):
					put_new_player(player)
					print("Thank you for saving")
					return player.player_data()

				else:
					print("Understood, continuing the game without saving, save prompts will be brought up again")
					return player.player_data()

