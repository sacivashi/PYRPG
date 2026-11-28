"""Bomber: the Small bomb passive, the bomb itself, its worthless price, and the Bomb-throwing unlock"""
from combat import combat as combat_module
from combat.combat import Combat, craft_role_item
from items.items_data import get_buyable_items, get_droppable_items, get_item_price
from players.player_data import PlayerData
from roles.roles import Roles

STATS = {'Strength': 0, 'Agility': 4, 'Intelligence': 7, 'Charisma': 1, 'Defense': 6, 'Magic': 0, 'Luck': -8}


def bomber(level=1, loot=None):
    return PlayerData(name="B", role="bomber", level=level, hp=22, stats=dict(STATS), max_hp=22,
                      loot=list(loot or []))


def test_bomber_is_a_role():
    assert "bomber" in Roles.data


def test_passive_gives_one_small_bomb(capsys):
    pd = bomber()
    craft_role_item(pd)
    craft_role_item(pd)
    assert pd.loot.count("Small bomb") == 1
    assert "put together a Small bomb" in capsys.readouterr().out


def test_other_roles_get_nothing():
    pd = bomber()
    pd.role = "warrior"
    craft_role_item(pd)
    assert pd.loot == []


def test_small_bomb_damage_scales_with_level():
    assert Combat.small_bomb_damage(1) == 7
    assert Combat.small_bomb_damage(3) == 7
    assert Combat.small_bomb_damage(10) == 18


def test_small_bomb_sears_one_enemy(monkeypatch):
    combat = Combat(bomber(level=10, loot=["Small bomb"]), "Slime", group_size=2)
    for enemy in combat.enemies:
        enemy.hp = enemy.max_hp = 100
        enemy.corruption = 5          # searing ignores corruption (and Defense)
    answers = iter(["1", "2"])        # the item, then enemy #2
    monkeypatch.setattr("builtins.input", lambda *_: next(answers))
    assert combat.use_item() == "end_turn"
    assert [e.hp for e in combat.enemies] == [100, 82]
    assert "Small bomb" not in combat.player.loot


def test_small_bomb_is_worthless():
    assert get_item_price("Small bomb") == 0
    assert "Small bomb" not in [name for name, _ in get_buyable_items()]
    assert "Small bomb" not in [name for name, _ in get_droppable_items()]


def test_merchants_wont_take_it(monkeypatch, capsys):
    from adventures.encounters import _sell_to_merchant
    from game.pyrpg import PYRPG
    game = PYRPG.__new__(PYRPG)
    game.player_data = bomber(loot=["Small bomb"])
    assert _sell_to_merchant(game) is None
    assert "nothing (left) to sell" in capsys.readouterr().out


def test_throwing_bombs_counts_toward_the_unlock(monkeypatch):
    recorded = []
    monkeypatch.setattr("unlocks.unlocks.record", lambda kind, value=None, amount=1, role=None: recorded.append((kind, value, amount)))

    def run(self):
        self.bombs_thrown = 2
        return ("victory", 10, 10)
    monkeypatch.setattr(Combat, "run_combat", run)
    pd = bomber()
    pd.role = "warrior"
    combat_module.start_combat(pd, "Slime")
    assert ("use", "Bomb", 2) in recorded
