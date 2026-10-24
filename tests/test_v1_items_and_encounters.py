import combat.combat as combat_module
from combat.combat import Combat, Enemy, start_combat
from enemies.enemies_data import (DEATH, death_chance, encounter_target_ratio, get_encounter_enemy,
                                  get_encounter_weights, get_enemy_stats)
from game.pyrpg import PYRPG
from players.player_data import PlayerData

STATS = {'Strength': 5, 'Agility': 5, 'Intelligence': 5, 'Defence': 5, 'Magic': 5, 'Luck': 5}


def make_pd(**overrides):
    defaults = dict(name="T", role="warrior", level=1, hp=99, stats=dict(STATS), max_hp=99)
    defaults.update(overrides)
    return PlayerData(**defaults)


def make_game(**overrides):
    game = PYRPG.__new__(PYRPG)
    game.player_data = make_pd(**overrides)
    return game


def answer(monkeypatch, *responses):
    replies = iter(responses)
    monkeypatch.setattr("builtins.input", lambda *_: next(replies, "4"))


# --- combat items --------------------------------------------------------------------------------

def test_items_used_in_combat_stay_used_after_the_fight(monkeypatch):
    pd = make_pd(loot=["Bomb", "Dagger"])

    def fake_run(self):
        self.player.loot.remove("Bomb")
        return "victory", 99, 20
    monkeypatch.setattr(Combat, "run_combat", fake_run)

    start_combat(pd, "Bandit")
    assert pd.loot == ["Dagger"]


def test_timer_bonus_turn_doesnt_tick_its_own_cooldown(monkeypatch):
    combat = Combat(make_pd(loot=["Timer"]), "Dragon")
    combat.current_turn = "player"
    answer(monkeypatch, "5", "1")          # use item #1 (Timer)
    combat.player_turn()
    assert combat.timer_cooldown == 6 and combat.bonus_turn

    answer(monkeypatch, "4")               # the bonus turn: skip
    combat.player_turn()
    assert combat.timer_cooldown == 6
    answer(monkeypatch, "4")               # next real turn ticks it
    combat.player_turn()
    assert combat.timer_cooldown == 5


def test_health_potion_heals_20_and_is_used_up(monkeypatch):
    combat = Combat(make_pd(loot=["Health potion"]), "Bandit")
    combat.player.current_hp = 1
    answer(monkeypatch, "1")
    combat.use_item()
    assert combat.player.current_hp == 21
    assert combat.player.loot == []


def test_thunder_apprentice_once_per_fight_and_evolves_after_6_uses(monkeypatch):
    pd = make_pd(loot=["Thunder apprentice"], item_state={"thunder apprentice": 5})
    combat = Combat(pd, "Dragon")
    answer(monkeypatch, "1")
    assert combat.use_item() == "end_turn"
    assert combat.player.loot == ["Thunder disciple"]
    assert "thunder apprentice" not in combat.player.item_state

    combat = Combat(make_pd(loot=["Thunder apprentice"]), "Dragon")
    answer(monkeypatch, "1", "1")
    combat.use_item()
    assert combat.use_item() is None          # second use this fight refused
    assert combat.player.item_state["thunder apprentice"] == 1


def test_dice_machine_is_reusable_6_times_per_fight(monkeypatch):
    combat = Combat(make_pd(loot=["Dice machine"]), "Dragon")
    monkeypatch.setattr("builtins.input", lambda *_: "1")
    results = [combat.use_item() for _ in range(7)]
    assert results[:6] == ["end_turn"] * 6
    assert results[6] is None
    assert combat.player.loot == ["Dice machine"]


def test_berserker_armor_grows_strength_while_at_or_below_half_hp():
    combat = Combat(make_pd(equipped="Berserker armor", hp=99), "Bandit")
    base = combat.player.stats['Strength']
    combat._berserker_check()
    assert combat.player.stats['Strength'] == base           # above half: nothing
    combat.player.current_hp = combat.player.max_hp // 2
    combat._berserker_check()
    combat._berserker_check()
    assert combat.player.stats['Strength'] == base + 2


# --- out of combat -------------------------------------------------------------------------------

def test_sleight_of_stats_grants_a_point_every_3_wins(monkeypatch):
    game = make_game(equipped="Sleight of stats")
    monkeypatch.setattr("game.pyrpg.random.choice", lambda seq: "Luck")
    for _ in range(3):
        game._sleight_of_stats_progress()
    assert game.player_data.stats['Luck'] == 6
    assert game.player_data.item_state["sleight of stats"] == {"wins": 0, "gains": {"Luck": 1}}


def test_sleight_of_stats_caps_at_10_per_stat(monkeypatch):
    game = make_game(equipped="Sleight of stats",
                     item_state={"sleight of stats": {"wins": 2, "gains": {s: 10 for s in STATS}}})
    game._sleight_of_stats_progress()
    assert game.player_data.stats == STATS


def test_an_old_save_wearing_the_dice_machine_gets_it_unequipped():
    game = make_game(equipped="Dice machine", loot=["Dice machine"])
    game._unequip_consumable()
    assert game.player_data.equipped is None
    assert game.player_data.loot == ["Dice machine"]


def test_potions_are_always_in_the_shop_at_15_gold(monkeypatch):
    game = make_game(gold=20)
    monkeypatch.setattr("builtins.input", lambda *_: "")
    assert game._buy("Health potion", 15, has_voucher=False)
    assert game.player_data.gold == 5 and game.player_data.loot == ["Health potion"]


# --- encounters ----------------------------------------------------------------------------------

def test_depth_target_ratio_ramps_through_the_tiers():
    from pytest import approx
    assert encounter_target_ratio(0) == encounter_target_ratio(1) == 0.25
    assert encounter_target_ratio(3) == 0.5 and encounter_target_ratio(5) == 0.75
    assert encounter_target_ratio(6) == 0.75 and encounter_target_ratio(10) == approx(1.2)
    assert encounter_target_ratio(13) == approx(1.6)            # halfway through 1.2 -> 2.0
    assert encounter_target_ratio(16) == 2.0 and encounter_target_ratio(20) == 2.5
    assert encounter_target_ratio(21) == 2.5 and encounter_target_ratio(50) == 3.5
    assert encounter_target_ratio(500) == 3.5                   # capped past depth 50
    ratios = [encounter_target_ratio(d) for d in range(0, 60)]
    assert ratios == sorted(ratios)                             # never gets easier going deeper


def test_death_is_never_in_the_regular_pool():
    assert DEATH not in {name for name, _ in get_encounter_weights(31, depth=500)}


def test_death_only_appears_from_depth_100(monkeypatch):
    assert death_chance(99) == 0
    assert death_chance(100) == 1
    assert death_chance(150) == 51
    assert death_chance(500) == 100
    monkeypatch.setattr("enemies.enemies_data.random.randint", lambda a, b: 1)
    assert get_encounter_enemy(31, depth=100) == DEATH
    assert get_encounter_enemy(31, depth=99) != DEATH


def test_you_cannot_flee_from_death(monkeypatch):
    combat = Combat(make_pd(), DEATH)
    combat.current_turn = "player"
    answer(monkeypatch, "6", "4")             # try to flee (refused), then skip
    combat.player_turn()
    assert combat.player_fled is False


def test_past_depth_50_positive_enemy_stats_grow():
    base = get_enemy_stats("Zombie")          # Corruption 8, HP 20, Attack 3, Defense 0, Speed -2, Luck -2
    buffed = Enemy("Zombie", depth=60).stats
    assert buffed["HP"] == base["HP"] + 10
    assert buffed["Corruption"] == base["Corruption"] + 10
    assert buffed["Defense"] == 0             # zero stays zero
    assert buffed["Speed"] == base["Speed"]   # negatives untouched
    assert Enemy("Zombie", depth=50).stats == base


def test_combat_uses_the_players_depth_for_enemy_buffs():
    combat = Combat(make_pd(distance=70), "Bandit")
    assert combat.enemies[0].max_hp == get_enemy_stats("Bandit")["HP"] + 20


# --- Manage Loot menu ----------------------------------------------------------------------------

def test_zero_backs_out_of_the_loot_menu_without_unequipping(monkeypatch):
    game = make_game(loot=["Dagger"], equipped="Dagger")
    monkeypatch.setattr("builtins.input", lambda *_: "0")
    game.manage_loot()
    assert game.player_data.equipped == "Dagger"


def test_u_unequips(monkeypatch):
    game = make_game(loot=["Dagger"], equipped="Dagger")
    answer(monkeypatch, "u", "")
    game.manage_loot()
    assert game.player_data.equipped is None
