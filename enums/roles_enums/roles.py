from game_data.roles_enums.role_descs import Descriptions
from game_data.data_actions.extracts.rolesextract import RolesExtract as stats
from game_data.data_actions.extracts.rolesextract import ByRole

# enums for later use


class Roles:
	_stats = stats.get_role_stats_by_name()
	warrior = _stats[ByRole.WARRIOR], Descriptions.WARRIOR_DESC
	mage = _stats[ByRole.MAGE], Descriptions.MAGE_DESC
	thief = _stats[ByRole.THIEF], Descriptions.THIEF_DESC
	druid = _stats[ByRole.DRUID], Descriptions.DRUID_DESC
	ranger = _stats[ByRole.RANGER], Descriptions.RANGER_DESC
	necromancer = _stats[ByRole.NECROMANCER], Descriptions.NECROMANCER_DESC
	forsaken = _stats[ByRole.FORSAKEN], Descriptions.FORSAKEN_DESC
	monk = _stats[ByRole.MONK], Descriptions.MONK_DESC
	data = {
		ByRole.WARRIOR: warrior,
		ByRole.MAGE: mage,
		ByRole.THIEF: thief,
		ByRole.DRUID: druid,
		ByRole.RANGER: ranger,
		ByRole.NECROMANCER: necromancer,
		ByRole.FORSAKEN: forsaken,
		ByRole.MONK: monk
	}

	@staticmethod
	def choose_role(role):
		return Roles.data.get(role)
		