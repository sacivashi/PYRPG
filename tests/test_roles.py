from roles.roles import Roles
from roles.roles_data import RolesExtract


def test_every_role_in_the_csv_has_a_description():
    # Building Roles looks up <ROLE>_DESC for every role in roles.csv — a role added to the CSV
    # without a description crashes the game at the role prompt, before anything else runs.
    for role in RolesExtract.get_role_stats_by_name():
        assert Roles.choose_role(role).description


def test_every_role_can_be_picked_at_the_prompt():
    # The role prompt lowercases what you type, so a capitalised name in roles.csv can never match
    assert all(role == role.lower() for role in RolesExtract.get_role_stats_by_name())
