from common_ops.player_data import PlayerData


class NewPlayer:
    # NewPlayer class for creating new players, gathering input and calculating HP
    def __init__(self, name):
        from game_data.data_inputs.input_role.input_role import InputRole
        from game_data.data_actions.extracts.rolesextract import RolesExtract

        self.name = name.title()
        self.role = InputRole.choose_role()
        self.level = 1
        self.stats = RolesExtract.get_role_stats_by_name()[self.role]
        self.hp = abs((int(self.stats['Strength']) + int(self.stats['Defence'])) / 0.2)

    def player_data(self):
        return PlayerData(name=self.name, role=self.role, level=self.level, hp=self.hp, stats=self.stats)
