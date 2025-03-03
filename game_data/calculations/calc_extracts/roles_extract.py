import csv
import os

classes_file = r"/stats/roles_x_stats/classes.csv"


def get_all_roles():
    if not os.path.exists(classes_file):
        print("No data file found.")
        return []

    roles = set()  # Use a set to avoid duplicates

    with open(classes_file, newline='', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            if row["Class"]:  # Avoid empty values
                roles.add(row["Class"])

    return list(roles)


def load_role(role):
    """Finds the role name in the CSV and returns it if found."""
    with open(classes_file, newline='', encoding='utf-8') as roles:
        reader = csv.DictReader(roles)
        for row in reader:
            class_name = row.get('Class', '').strip().lower()  # Ensure it's a string
            if class_name == role.lower():
                return class_name  # Return role name for lookup
    return None  # Role not found


def load_stats(role_name):
    """Loads class stats for a specific role."""
    with open(classes_file, newline='', encoding='utf-8') as stats:
        reader = csv.DictReader(stats)
        for row in reader:
            if row.get('Class', '').strip().lower() == role_name:
                return {stat: int(row[stat]) for stat in row if stat != 'Class'}
    return None  # Role stats not found


def extract_stats(desired_role):
    """Extracts stats using both load functions."""
    role_name = load_role(desired_role)
    if role_name:
        return (f"{role_name} stats: {load_stats(role_name)}")
    else:
        return (f"Role '{desired_role}' was not found")


# Enum for e, more will be added in the future
class Role:
    WARRIOR = 'warrior'
    MAGE = 'mage'
    THIEF = 'thief'
    DRUID = 'druid'
    RANGER = 'ranger'
    NECROMANCER = 'necromancer'
