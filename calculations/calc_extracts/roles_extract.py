import csv

classes_file = r"D:\PYRPG\stats\roles_x_stats\classes.csv"


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
        print(f"{role_name} stats: {load_stats(role_name)}")
    else:
        print(f"Role '{desired_role}' was not found")


class Role:
    WARRIOR = 'warrior'
    MAGE = 'mage'
    THIEF = 'thief'
    DRUID = 'druid'
    RANGER = 'ranger'
    NECROMANCER = 'necromancer'
