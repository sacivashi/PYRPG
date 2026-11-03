from util.file_io import get_data, read_csv


class RolesExtract:
    @staticmethod
    def get_role_names():
        return [row["Class"] for row in read_csv(get_data("roles_csv"))]

    @staticmethod
    def get_role_stats_by_name():
        # {class: {stat: value}} — every column but Class is a stat
        return {row["Class"]: {stat: int(value) for stat, value in row.items() if stat != "Class"}
                for row in read_csv(get_data("roles_csv"))}

    @staticmethod
    def get_highest_stat_value(role_stats):
        # Exclude 'Defense' since it's not an offensive stat
        stats_without_defence = {k: v for k, v in role_stats.items() if k != "Defense"}

        # Find and return the highest stat value
        return max(stats_without_defence.values())
