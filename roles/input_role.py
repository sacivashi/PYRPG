from roles.roles_data import RolesExtract
from roles.roles import Roles
from unlocks.unlocks import locked_names, locked_role_lines


class InputRole:
    @staticmethod
    def choose_role():
        locked = locked_names("class")  # v1.0.7: some classes have to be unlocked first
        roles = {role: stats for role, stats in RolesExtract.get_role_stats_by_name().items()
                 if role.lower() not in locked}

        print("\nChoose a role:")
        print("  " + ", ".join(roles))
        hints = locked_role_lines()
        if hints:
            print("\nLocked:")
            print("\n".join(hints))

        while True:
            player_input = input("\nRole: ").strip().lower()

            if player_input in roles:
                stats_display = ", ".join(f"{stat}: {value}" for stat, value in roles[player_input].items())
                confirm = input(f"You chose {player_input.title()}. {Roles.choose_role(player_input).description}\n"
                                f"Stats: {stats_display}\n"
                                f"Are you sure you want this role? (yes/no): ").strip().lower()
                if confirm in ("yes", "y"):
                    print(f"{player_input.title()} locked in!")
                    return player_input
                else:
                    print("Okay, let's choose again.\n")
            else:
                print(f"Invalid role. Please choose one of: {', '.join(roles)}")
