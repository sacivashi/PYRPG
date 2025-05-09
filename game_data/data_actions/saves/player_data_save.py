import csv

from common_ops.common_ops import get_data, read_csv


def save_new_player(new_player_obj):
    players_csv_path = get_data("players_csv")
    csv_data = read_csv(players_csv_path)

    # Unpack player data
    name, role, level, hp, stats = new_player_obj.player_data()

    # Check if headers already exist
    if csv_data:
        headers = csv_data[0]
    else:
        headers = ["name", "role", "level", "HP"] + list(stats.keys())
        csv_data.append(headers)

    new_row = [name.title(), role, level, int(hp)] + [stats[stat] for stat in stats]

    with open(players_csv_path, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(new_row)

    print(f"Player '{name}' saved successfully!")