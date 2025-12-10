import csv

from common_ops.common_ops import get_data, read_csv


def save_new_player(new_player_obj):
    players_csv_path = get_data("players_csv")
    csv_data = read_csv(players_csv_path)

    # Unpack player data
    name, role, level, hp, stats = new_player_obj.player_data()
    name = name.title()  # Normalize name case

    # Build headers if missing
    if not csv_data:
        headers = ["name", "role", "level", "HP"] + list(stats.keys())
        csv_data.append(headers)
    else:
        headers = csv_data[0]

    new_row = [name, role, level, int(hp)] + [stats[stat] for stat in stats]

    # Find existing player row (if exists), else append
    found = False
    for i in range(1, len(csv_data)):
        if csv_data[i][0].lower() == name.lower():
            csv_data[i] = new_row
            found = True
            break

    if not found:
        csv_data.append(new_row)

    # Write back to CSV (overwrite)
    with open(players_csv_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(csv_data)

    print(f"Player '{name}' {'updated' if found else 'saved'} successfully!")
