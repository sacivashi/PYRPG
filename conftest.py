# Its presence tells pytest that the project root has no __init__.py, so pytest adds this directory
# to sys.path when collecting tests — letting test files use the same root-relative imports as the
# game itself (e.g. `from combat.combat_player import Player`).
import pytest


@pytest.fixture(autouse=True)
def _own_unlocks_file(tmp_path, monkeypatch):
    """Unlock progress is shared by every character (data/unlocks.json) and written whenever
    something counts toward it — point every test at its own empty file instead of the real one."""
    monkeypatch.setenv("unlocks_json", str(tmp_path / "unlocks.json"))
