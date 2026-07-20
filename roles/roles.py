from dataclasses import dataclass

from roles.role_descriptions import Descriptions
from roles.roles_data import RolesExtract as stats

# enums for later use


@dataclass(frozen=True)
class Role:
	stats: dict
	description: str


class Roles:
	_stats = stats.get_role_stats_by_name()
	# Convention: role name "warrior" maps to Descriptions.WARRIOR_DESC.
	# Fails loudly (AttributeError) if a role's description is missing, instead of
	# silently dropping the role from Roles.data.
	data = {
		role_name: Role(role_stats, getattr(Descriptions, f"{role_name.upper()}_DESC"))
		for role_name, role_stats in _stats.items()
	}

	@classmethod
	def choose_role(cls, role="warrior"):
		return cls.data.get(role)
