import game_data.calculations.calc_extracts.roles_extract as role_extract
from game_data.data_inputs.input_role.input_role import Input_Role


class New_Character:
    def __init__(self, name):
        self.name = name
        self.role = Input_Role.input_role()  # Get role input from the player
        self.stats = role_extract.Roles_Extract.extract_stats(self.role)  # Get stats based on role
        self.level = 1  # Default starting level
        self.hp = int((self.stats["Strength"] / 2) + (self.stats["Defence"] + 4))  # HP Calculation

    def get_character_data(self):
        """Return all character data as a dictionary (for easy saving)."""
        return {
            "Name": self.name,
            "Role": self.role,
            "Level": self.level,
            "HP": self.hp,
            "Stats": str(self.stats)  # Convert dictionary to string for CSV storage
        }
