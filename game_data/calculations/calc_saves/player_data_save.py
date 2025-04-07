import csv
import os

data_file = r"C:\PYRPG\game_data\players_data\players.csv"


def save_player_data(Name, Role, Level, HP, Stats):
    fieldnames = ["Name", "Role", "Level", "HP", "Stats"]
    rows = []

    # Check if the file exists
    if os.path.exists(data_file):
        with open(data_file, newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            rows = list(reader)  # Convert reader to a list of dictionaries

    # Check if player exists, if yes, update it
    for row in rows:
        if row["Name"] == Name:
            row["Role"] = Role
            row["Level"] = str(Level)
            row["HP"] = str(HP)
            row["Stats"] = Stats
            break
    else:
        # If player is not found, add a new row
        rows.append({"Name": Name, "Role": Role, "Level": str(Level), "HP": str(HP), "Stats": Stats})

    # Write everything back to the CSV
    with open(data_file, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Player '{Name}' data saved successfully!")

