from game_data.roles_enums.role_descs import Descriptions
from game_data.data_actions.extracts.rolesextract import RolesExtract as stats
from game_data.data_actions.extracts.rolesextract import ByRole

# enums for later use


class Roles:
	_stats = stats.get_role_stats_by_name()
	warrior = _stats[ByRole.WARRIOR], Descriptions.warrior
	mage = _stats[ByRole.MAGE], Descriptions.mage
	thief = _stats[ByRole.THIEF], Descriptions.thief
	druid = _stats[ByRole.DRUID], Descriptions.druid
	ranger = _stats[ByRole.RANGER], Descriptions.ranger
	necromancer = _stats[ByRole.NECROMANCER], Descriptions.necromancer
	forsaken = _stats[ByRole.FORSAKEN], Descriptions.forsaken
	monk = _stats[ByRole.MONK], Descriptions.monk
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
		