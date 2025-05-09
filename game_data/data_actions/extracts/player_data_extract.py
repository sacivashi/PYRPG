from game_data.data_inputs.input_role.input_role import InputRole
from game_data.data_actions.extracts.rolesextract import RolesExtract


class NewPlayer:
    def __init__(self, name):
        self.name = name
        self.role_name = InputRole.choose_role()  # only called once!
        self.stats = RolesExtract.get_role_stats_by_name()[self.role_name]
        self.level = 1
        self.HP = ((int(self.stats['Strength']) + int(self.stats['Defence'])) / 0.2)

    def player_data(self):
        return self.name, self.role_name, self.level, self.HP, self.stats
