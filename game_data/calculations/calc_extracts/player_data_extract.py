import csv
import os

data_file = r"C:\PYRPG\game_data\players_data\players.csv"


def get_player_data(Name):
	# Check if the file exists
	if not os.path.exists(data_file):
		print("No data file found.")
		return None
	
	# Read CSV and look for the player
	with open(data_file, newline='', encoding='utf-8') as file:
		reader = csv.DictReader(file)
		for row in reader:
			if row["Name"] == Name:
				return row  # Return the whole row as a dictionary
	
	print(f"Player '{Name}' not found.")
	return None
