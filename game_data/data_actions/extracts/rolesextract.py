from common_ops.common_ops import get_data, read_csv


class RolesExtract:
    @staticmethod
    def get_role_names():
        roles_csv_path = get_data("roles_csv")  # get path from XML
        csv_data = read_csv(roles_csv_path)     # read CSV file
        return [row[0] for row in csv_data[1:] if row]  # skip header and take first column only

    @staticmethod
    def get_role_stats_by_name():
        roles_csv_path = get_data("roles_csv")
        csv_data = read_csv(roles_csv_path)

        headers = csv_data[0]            # ['name', 'strength', 'dexterity', ...]
        stat_keys = headers[1:]          # ['strength', 'dexterity', ...]

        role_stats = {}
        for row in csv_data[1:]:         # skip header
            if row:
                name = row[0]
                stats = {stat_keys[i]: int(row[i + 1]) for i in range(len(stat_keys))}
                role_stats[name] = stats

        return role_stats

    @staticmethod
    def get_highest_stat_value(role_stats):
        # Exclude 'vitality' if it's present in the stats
        stats_without_defence = {k: v for k, v in role_stats.items() if k != "Defence"}

        # Find and return the highest stat value
        return max(stats_without_defence.values())


class ByRole:
    WARRIOR = "warrior"
    MAGE = "mage"
    THIEF = "thief"
    DRUID = "druid"
    RANGER = "ranger"
    NECROMANCER = "necromancer"
    FORSAKEN = "forsaken"
    MONK = "monk"
