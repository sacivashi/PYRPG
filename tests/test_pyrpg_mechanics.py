from combat.combat_player import Player
from game.pyrpg import PYRPG
from players.player_data import PlayerData

BASE_STATS = {'Strength': 5, 'Agility': 5, 'Intelligence': 0, 'Defence': 5, 'Magic': 5, 'Luck': 5}


def make_game(**stat_overrides):
    """A PYRPG without running its interactive __init__."""
    game = PYRPG.__new__(PYRPG)
    game.player_data = PlayerData(name="T", role="warrior", level=1, hp=30, stats={**BASE_STATS, **stat_overrides})
    return game


def test_rest_chance_has_a_30_percent_floor():
    # Luck + 15 stays at or under 30 until Luck 15, so every stock role (Luck 1-9) sits on the floor
    for luck in (0, 5, 9, 15):
        assert make_game(Luck=luck).calculate_rest_chance() == 30


def test_rest_chance_is_luck_plus_15_between_floor_and_cap():
    assert make_game(Luck=16).calculate_rest_chance() == 31
    assert make_game(Luck=20).calculate_rest_chance() == 35
    assert make_game(Luck=30).calculate_rest_chance() == 45


def test_rest_chance_is_capped_at_60():
    for luck in (45, 100):
        assert make_game(Luck=luck).calculate_rest_chance() == 60


def test_negative_luck_always_rests_worse_than_zero_luck():
    baseline = make_game(Luck=0).calculate_rest_chance()
    for luck in (-1, -5, -10, -30):
        assert make_game(Luck=luck).calculate_rest_chance() < baseline


def test_negative_luck_rest_chance_drops_from_25_toward_a_15_floor():
    assert make_game(Luck=-1).calculate_rest_chance() == 24.5
    assert make_game(Luck=-10).calculate_rest_chance() == 20.2
    assert make_game(Luck=-20).calculate_rest_chance() == 15.4


def test_negative_luck_rest_chance_floors_at_15():
    for luck in (-21, -40, -500):
        assert make_game(Luck=luck).calculate_rest_chance() == 15


def test_negative_magic_earns_15_percent_less_exp():
    normal = make_game(Magic=5).calculate_exp_reward("Bandit")
    cursed = make_game(Magic=-5).calculate_exp_reward("Bandit")
    assert cursed == normal * 0.85


def test_zero_magic_is_not_penalised():
    assert make_game(Magic=0).calculate_exp_reward("Bandit") == make_game(Magic=5).calculate_exp_reward("Bandit")


def test_player_power_is_sum_of_absolute_effective_stats():
    game = make_game(Strength=-3)  # -3 + 5 + 0 + 5 + 5 + 5 -> 3 + 5 + 0 + 5 + 5 + 5
    game.player_data.equipped = None
    assert game._player_power() == 23


# --- Gear must count everywhere, not just in combat -------------------------------------------
# apply_equipment is patched so these tests don't depend on what's in items.csv.

def with_gear(monkeypatch, **deltas):
    """Pretend the player wears gear giving these stat deltas."""
    def fake_apply_equipment(base_stats, equipped_name, dice_roll=None):
        effective = dict(base_stats)
        for stat, delta in deltas.items():
            effective[stat] = effective.get(stat, 0) + delta
        return effective
    monkeypatch.setattr(Player, "apply_equipment", staticmethod(fake_apply_equipment))


def test_gear_luck_counts_for_rest_odds(monkeypatch):
    game = make_game(Luck=5)
    assert game.calculate_rest_chance() == 30          # base Luck 5 -> floor
    with_gear(monkeypatch, Luck=15)
    assert game.calculate_rest_chance() == 35          # Luck 20 -> 20 + 15


def test_gear_luck_counts_for_loot_drop_chance(monkeypatch):
    game = make_game(Luck=5)
    assert game.calculate_loot_drop_chance() == 27.5
    with_gear(monkeypatch, Luck=10)
    assert game.calculate_loot_drop_chance() == 42.5   # Luck 15 -> 20 + 22.5


def test_gear_luck_counts_for_gold(monkeypatch):
    game = make_game(Luck=5)
    with_gear(monkeypatch, Luck=95)                    # Luck 100 -> low = max(5, 42) = 42
    assert min(game.calculate_gold_reward() for _ in range(200)) >= 42


def test_gear_intelligence_counts_for_exp(monkeypatch):
    game = make_game(Intelligence=0)
    plain = game.calculate_exp_reward("Bandit")
    with_gear(monkeypatch, Intelligence=50)            # +50% EXP
    assert game.calculate_exp_reward("Bandit") == plain * 1.5


def test_gear_that_pushes_magic_negative_triggers_the_exp_penalty(monkeypatch):
    game = make_game(Magic=5)
    plain = game.calculate_exp_reward("Bandit")
    with_gear(monkeypatch, Magic=-10)                  # effective Magic -5
    assert game.calculate_exp_reward("Bandit") == plain * 0.85


def test_max_hp_growth_uses_gear_adjusted_stats(monkeypatch):
    game = make_game()                                 # Str 5, Def 5 -> max HP floor of 22
    game.player_data.hp = 22
    game.player_data.max_hp = 22
    with_gear(monkeypatch, Defence=10)                 # effective Def 15 -> 39 max HP
    game._sync_max_hp_after_growth()
    assert game.player_data.max_hp == 39
    assert game.player_data.hp == 39                   # healed by the 17 it grew
