import csv
import random

enemies_file = r'/stats/enemies_x_stats/enemies.csv'


def load_enemy_names(file_path):
    enemies = []
    with open(file_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            enemies.append(row['Name'])  # Store only names
    return enemies


def get_random_enemy(file_path):
    enemies = load_enemy_names(file_path)
    return random.choice(enemies) if enemies else None  # Pick a random enemy


random_enemy = get_random_enemy(enemies_file)

