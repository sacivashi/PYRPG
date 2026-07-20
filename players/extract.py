from combat.combat_player import Player


class NewPlayer(Player):
    # NewPlayer class for creating new players, gathering input and calculating HP
    def __init__(self, name):
        from roles.input_role import InputRole
        from roles.roles_data import RolesExtract

        role = InputRole.choose_role()
        stats = RolesExtract.get_role_stats_by_name()[role]
        super().__init__(name.title(), role, 1, stats)
