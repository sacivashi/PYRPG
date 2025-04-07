import csv
import random

enemies_file = r"C:\PYRPG\game_data\stats\enemies_x_stats\enemies.csv"


# Base stat loader
def load_enemies():
	"""Loads all enemies into a dictionary."""
	enemies = {}
	with open(enemies_file, newline='', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		for row in reader:
			enemy_name = row['Name'].lower()
			enemies[enemy_name] = {
				"BaseHP": int(row['HP']),
				"BaseAttack": int(row['Attack']),
				"BaseDefense": int(row['Defense']),
				"BaseSpeed": int(row['Speed']),
				"BaseLuck": int(row['Luck'])
			}
	return enemies


# enemy scale based on player's level (calculations might change)
def scale_enemy(enemy_name, player_level):
	"""Scales enemy stats based on player level."""
	enemies = load_enemies()
	
	if enemy_name.lower() not in enemies:
		return f"Enemy '{enemy_name}' not found!"
	
	base_stats = enemies[enemy_name.lower()]
	
	# Scaling formula (adjust as needed)
	scale_factor = 1 * (player_level * 0.1)  # 10% increase per level
	scaled_enemy = {
			"HP": int((base_stats["BaseHP"] * scale_factor) + (scale_factor * 3)) + int(player_level // 1.5),
			"Attack": int((base_stats["BaseAttack"] * scale_factor) / 0.5) + int(player_level // 1.5),
			"Defense": int((base_stats["BaseDefense"] / 3) * (scale_factor + 2)) + int(player_level // 1.5),
			"Speed": int((base_stats["BaseSpeed"] / 1.5) + (scale_factor * 1.5)) + int(player_level // 1.5),
			"Luck": int(base_stats["BaseLuck"] + (1 + (scale_factor * 0.05))) + int(player_level // 1.5)
		}
	
	return scaled_enemy


def spawn_random_enemy(player_level):
	"""Spawns a random enemy and scales it based on player level."""
	enemies = load_enemies()
	random_enemy_name = random.choice(list(enemies.keys()))
	print(random_enemy_name, scale_enemy(random_enemy_name, player_level))

