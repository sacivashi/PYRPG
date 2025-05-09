from game_data.data_actions.extracts.rolesextract import RolesExtract
from game_data.roles_enums.roles import Roles


class InputRole:
    @staticmethod
    def choose_role():
        roles = RolesExtract.get_role_stats_by_name()

        while True:
            player_input = input(f"Choose a role {RolesExtract.get_role_names()}: ").strip().lower()

            if player_input in roles:
                confirm = input(f"You chose {player_input.title()}. {Roles.choose_role(player_input)}\n"
                                f"Are you sure you want this role? (yes/no): ").strip().lower()
                if confirm in ("yes", "y"):
                    print(f"{player_input.title()} locked in!")
                    return player_input
                else:
                    print("Okay, let's choose again.\n")
            else:
                print("Invalid role. Please choose a valid role.\n")

