from game_data.roles_enums.role_descs import Descriptions
import game_data.calculations.calc_extracts.roles_extract as stats
from game_data.calculations.calc_extracts.roles_extract import Role

# enums for later use


class Roles:
	warrior = stats.extract_stats(Role.WARRIOR), Descriptions.warrior
	mage = stats.extract_stats(Role.MAGE), Descriptions.mage
	thief = stats.extract_stats(Role.THIEF), Descriptions.thief
	druid = stats.extract_stats(Role.DRUID), Descriptions.druid
	ranger = stats.extract_stats(Role.RANGER), Descriptions.ranger
	necromancer = stats.extract_stats(Role.NECROMANCER), Descriptions.necromancer
	
	
def choose_role(role):
	if role == Role.WARRIOR:
		return Roles.warrior
	elif role == Role.MAGE:
		return Roles.mage
	elif role == Role.THIEF:
		return Roles.thief
	elif role == Role.DRUID:
		return Roles.druid
	elif role == Role.RANGER:
		return Roles.ranger
	elif role == Role.NECROMANCER:
		return Roles.necromancer
		
		