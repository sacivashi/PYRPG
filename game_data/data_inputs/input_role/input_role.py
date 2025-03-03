import game_data.calculations.calc_extracts.roles_extract as roles
from game_data.roles_enums.roles import choose_role


class Input_Role:
	@staticmethod
	def input_role():
		print(f"Available roles: {roles.get_all_roles()}")
		role_chosen = input("choose one (input the role's name): ".lower())
		print(choose_role(role_chosen))
		commit = input("Are you sure you want this role? (yes/no) ".lower())
		if commit == 'yes':
			your_role = role_chosen
		elif commit == 'no':
			Input_Role.input_role()
		return your_role
	