from common_ops.common_ops import get_data, read_csv
import random


def get_enemy_names():
    reader = read_csv(get_data("enemies_csv"))
    name = random.choice([row[0] for row in reader if row[0] != "Name"])
    return name


def get_enemy_stats(name):
    reader = read_csv(get_data("enemies_csv"))
    headers = reader[0]  # First row is the header
    for row in reader[1:]:  # Skip the header
        if row[0].lower() == name.lower():
            return {"Name": row[0],
                    **{
                        headers[i]: int(row[i]) if row[i].lstrip('-').isdigit() else row[i]
                        for i in range(1, len(headers))
                    }}
    return None


enemy = get_enemy_names()
enem_stats = get_enemy_stats(enemy)


