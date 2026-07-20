import xml.etree.ElementTree as ET
import csv
import os

# Navigate from util/file_io.py up to the project root
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_xml_path = os.path.join(_project_root, "data", "config.xml")


def get_data(node_name):
    root = ET.parse(_xml_path).getroot()
    node = root.find('.//' + node_name)
    if node is None or node.text is None:
        raise ValueError(f"No '{node_name}' entry found in {_xml_path}")
    return os.path.join(_project_root, node.text)


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
