import xml.etree.ElementTree as ET
import csv


def get_data(node_name):
    root = ET.parse(r"D:\PYRPG\game_data\xml_db\data.xml").getroot()
    return root.find('.//' + node_name).text


def read_csv(file_name):
    data = []
    with open(file_name, newline='') as file:
        reader = csv.reader(file)
        for row in reader:
            data.insert(len(data), row)
        return data


def check_existing_player(player_name):
    players_csv_path = get_data("players_csv")
    csv_data = read_csv(players_csv_path)

    headers = csv_data[0]  # ['name', 'role', 'level', 'HP', 'strength', ...]
    stat_keys = headers[4:]

    for row in csv_data[1:]:
        if row and row[0].strip().lower() == player_name.strip().lower():
            role = row[1]
            level = int(row[2])

            stats = {stat_keys[i]: int(row[i + 4]) for i in range(len(stat_keys))}

            return {
                "exists": True,
                "name": player_name,
                "role": role,
                "level": level,
                "stats": stats
            }

    return {
        "exists": False,
        "name": player_name
    }
