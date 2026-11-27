# Its presence tells pytest that the project root has no __init__.py, so pytest adds this directory
# to sys.path when collecting tests — letting test files use the same root-relative imports as the
# game itself (e.g. `from combat.combat_player import Player`).
import pytest

TEST_PLAYER = "Tester"


@pytest.fixture(autouse=True)
def _own_save_file(tmp_path, monkeypatch):
    """Saves and unlock progress go to the active player's entry in data/players.json, written
    whenever something counts toward an unlock — point every test at its own empty file instead
    of the real one, playing as TEST_PLAYER."""
    monkeypatch.setenv("players_json", str(tmp_path / "players.json"))
    monkeypatch.setenv("unlocks_json", str(tmp_path / "unlocks.json"))
    monkeypatch.setattr("players.profiles.ACTIVE", TEST_PLAYER)
