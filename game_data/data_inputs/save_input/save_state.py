import csv
import os

from game_data.calculations.calc_saves.player_data_save import save_player_data
from game_data.calculations.calc_extracts.player_data_extract import get_player_data  # Import the function
from game_data.new_character_calc.new_character import New_Character

data_file = r"D:\PYRPG\players_data\players.csv"


class Save_State:
    @staticmethod
    def save_state(name):
        # Check if player exists and ask if they want to load it
        player_data = get_player_data(name)  # Retrieve saved data if it exists
        if player_data:
            commit = input(
                f"Player '{name}' already exists. Would you like to load your saved data? (yes/no) ").strip().lower()
            if commit == "yes":
                print("Loading saved data...")
                return player_data  # Return the saved data instead of creating a new character
        
        # If they don't want to load, create a new character
        player = New_Character(name)
        commit = input(f"{name}, this project can save your data.\n"
                       "Would you like to save your character? (yes/no) ").strip().lower()
        
        if commit == "yes":
            player_data = player.get_character_data()  # Retrieve player data
            save_player_data(
                player_data["Name"],
                player_data["Role"],
                player_data["Level"],
                player_data["HP"],
                player_data["Stats"]
            )
            print("Character saved successfully.")
        else:
            print("Character not saved.")
