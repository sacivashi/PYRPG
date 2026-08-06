from combat.combat_player import Player
from players.player_data import PlayerData


class NewPlayer(Player):
    # NewPlayer class for creating new players, gathering input and calculating HP
    def __init__(self, name):
        from roles.input_role import InputRole
        from roles.roles_data import RolesExtract

        role = InputRole.choose_role()
        stats = RolesExtract.get_role_stats_by_name()[role]
        hp = Player.calculate_hp(stats)
        super().__init__(PlayerData(name.title(), role, 1, hp, stats, max_hp=hp))
