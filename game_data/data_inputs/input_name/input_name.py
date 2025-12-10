import time

from common_ops.common_ops import check_existing_player
from game_data.data_actions.extracts.player_data_extract import Player, NewPlayer
from game_data.data_actions.saves.player_data_save import save_new_player

player = None


class InputName:
	@staticmethod
	def input_name():
		global player

		while True:
			your_name = input(
				"""Welcome to PyRPG.
	This project is a text based RPG game.
	Please look at patch notes files to see new patches or features.
	To start you off, please input your name: """).strip()

			player_info = check_existing_player(your_name)
			if player_info["exists"]:
				existence = input("this player already exists, would you like to load your save file? (yes/no) ")
				if existence in ("y", "yes"):
					print(f"Welcome back, {player_info['name'].capitalize()}!")
					print(f"Role: {player_info['role'].capitalize()}, Level: {player_info['level']}")
					print("Stats:", player_info["stats"])
					return player_info
				# Skip role choosing
				else:
					print("PyRPG doesn't support duplicate names. Please choose a different name.\n")
					time.sleep(0.4)
			else:
				player = NewPlayer(your_name)
				playersave = input(f"{your_name.title()}, would you like to be added to the save files? (yes/no) ")
				if playersave in ('yes', 'y'):
					save_new_player(player)
					print("Thank you for saving")
					return player.player_data()

				else:
					print("Understood, continuing the game without saving, save prompts will be brought up again")
					return player.player_data()

