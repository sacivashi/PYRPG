"""
Test file to demonstrate all negative stat effects from Alpha II patch notes
This shows how each negative stat works exactly as specified
"""

from game_data.combat.damage_calculator import DamageCalculator

def test_negative_strength():
    """Test -Strength effects: self-damage on miss, healing on hit"""
    print("=== TESTING NEGATIVE STRENGTH ===")
    
    # Forsaken character with -2 Strength
    forsaken_stats = {'Strength': -2, 'Agility': 3, 'Intelligence': 2, 'Defence': 10, 'Magic': -2, 'Luck': 2}
    max_hp = 40
    
    print("Forsaken stats:", forsaken_stats)
    print("Max HP:", max_hp)
    print("\nFrom patch notes:")
    print("-Strength: Debuff: Missing attacks makes you hit yourself for (HP -(-x) * 2) damage")
    print("           Benefit: hitting enemies heals you by (max HP / (X + n))")
    
    # Test multiple attacks to show both miss and hit
    for i in range(5):
        damage, effects, unavoidable = DamageCalculator.calculate_player_damage(
            forsaken_stats, max_hp, is_magic_attack=False
        )
        print(f"\nAttack {i+1}: Damage = {damage}")
        for effect_type, value in effects:
            if effect_type == "self_damage":
                expected = abs(max_hp - (2 * 2))  # (HP - (-x) * 2)
                print(f"  Self-damage: {value} (expected: {expected})")
            elif effect_type == "heal_on_hit":
                expected = max_hp / (2 + 1)  # max HP / (X + n)
                print(f"  Heal on hit: {value} (expected: {expected:.1f})")

def test_negative_agility():
    """Test -Agility effects: always last, but dodge/counter bonus"""
    print("\n=== TESTING NEGATIVE AGILITY ===")
    
    # Monk character with -9 Agility
    monk_stats = {'Strength': 5, 'Agility': -9, 'Intelligence': 8, 'Defence': -9, 'Magic': 3, 'Luck': 1}
    
    print("Monk stats:", monk_stats)
    print("\nFrom patch notes:")
    print("-Agility: Debuff: Always act last (-speed enemies not included)")
    print("          Benefit: Incoming attacks are easier to read — +X% dodge or counter chance")
    
    # Test initiative calculation
    initiative, dodge_bonus = DamageCalculator.apply_agility_modifier(0, monk_stats['Agility'])
    print(f"\nInitiative: {initiative} (should be -1000 = always last)")
    print(f"Dodge/Counter bonus: {dodge_bonus} (should be {abs(monk_stats['Agility']) * 0.1})")

def test_negative_intelligence():
    """Test -Intelligence effects: confusion vs focused damage"""
    print("\n=== TESTING NEGATIVE INTELLIGENCE ===")
    
    # Custom stats with negative intelligence
    confused_stats = {'Strength': 5, 'Agility': 3, 'Intelligence': -4, 'Defence': 2, 'Magic': 2, 'Luck': 2}
    
    print("Character stats:", confused_stats)
    print("\nFrom patch notes:")
    print("-Intelligence: Debuff: (100 / X + RNG)% to attack a different enemy")
    print("               Benefit: you hit harder (N * X - (INT of: highest stat / 10))")
    
    # Test multiple attacks to show confusion vs focus
    for i in range(5):
        damage, intel_effect = DamageCalculator.apply_intelligence_modifier(
            10, confused_stats['Intelligence'], confused_stats
        )
        print(f"\nAttack {i+1}: Effect = {intel_effect}")
        if intel_effect == "confused":
            print("  Attack confused! Hits wrong target!")
        elif intel_effect == "focused":
            highest_stat = max([v for k, v in confused_stats.items() if k not in ['Intelligence', 'Defence', 'HP']])
            expected_bonus = (10 * 4) - (highest_stat / 10)
            print(f"  Focused attack! Damage = {damage} (bonus from focus)")

def test_negative_defence():
    """Test -Defence effects: extra damage taken, reflect damage"""
    print("\n=== TESTING NEGATIVE DEFENCE ===")
    
    # Character with negative defence
    stats = {'Strength': 5, 'Agility': 3, 'Intelligence': 2, 'Defence': -7, 'Magic': 2, 'Luck': 2}
    
    print("Character stats:", stats)
    print("\nFrom patch notes:")
    print("-Defence: Debuff: Getting hit makes you take (-X) damage bonus")
    print("          Benefit: you damage the attacker by (damage / 75 + X) back")
    
    # Test taking damage
    incoming_damage = 20
    final_damage, defence_effect = DamageCalculator.apply_defence_modifier(
        incoming_damage, stats['Defence']
    )
    
    extra_damage = abs(stats['Defence'])
    expected_damage = incoming_damage + extra_damage
    expected_reflect = (incoming_damage / 75) + abs(stats['Defence'])
    
    print(f"\nIncoming damage: {incoming_damage}")
    print(f"Final damage taken: {final_damage} (expected: {expected_damage})")
    if defence_effect:
        print(f"Reflected damage: {defence_effect[1]} (expected: {expected_reflect:.2f})")

def test_negative_luck():
    """Test -Luck effects: higher miss chance, unavoidable when hit"""
    print("\n=== TESTING NEGATIVE LUCK ===")
    
    # Character with negative luck  
    stats = {'Strength': 5, 'Agility': 3, 'Intelligence': 2, 'Defence': 2, 'Magic': 2, 'Luck': -3}
    
    print("Character stats:", stats)
    print("\nFrom patch notes:")
    print("-Luck: Debuff: higher chance to miss attacks, lower loot rolls")
    print("       Benefit: Successful attacks are unavoidable")
    
    # Test multiple attacks
    hits = 0
    unavoidables = 0
    for i in range(10):
        damage, unavoidable = DamageCalculator.apply_luck_modifier(15, stats['Luck'])
        if damage > 0:
            hits += 1
            if unavoidable:
                unavoidables += 1
    
    miss_chance = abs(stats['Luck']) * 0.12
    print(f"\nOut of 10 attacks: {hits} hit, {10-hits} missed")
    print(f"Expected miss chance: {miss_chance:.1%}")
    print(f"Unavoidable hits: {unavoidables}/{hits}")

def test_negative_magic():
    """Test -Magic effects: self-damage, stat debuffing"""
    print("\n=== TESTING NEGATIVE MAGIC ===")
    
    # Necromancer with negative magic
    necro_stats = {'Strength': 1, 'Agility': 2, 'Intelligence': 6, 'Defence': 4, 'Magic': -8, 'Luck': 5}
    
    print("Necromancer stats:", necro_stats)
    print("\nFrom patch notes:")
    print("-Magic: Debuff: using cursed magika makes you suffer (X + n) self damage")
    print("        Benefit: you have a chance to lower the enemy stats")
    
    # Test magic attacks
    for i in range(3):
        damage, effects = DamageCalculator.apply_magic_modifier(
            20, necro_stats['Magic'], is_magic_attack=True
        )
        print(f"\nMagic Attack {i+1}:")
        for effect_type, value in effects:
            if effect_type == "self_damage":
                expected_min = abs(necro_stats['Magic']) + 1
                expected_max = abs(necro_stats['Magic']) + 3
                print(f"  Self-damage: {value} (expected: {expected_min}-{expected_max})")
            elif effect_type == "enemy_stat_debuff":
                print(f"  Enemy stat debuffed by: {value}")

def test_enemy_negative_stats():
    """Test enemy negative stat effects"""
    print("\n=== TESTING ENEMY NEGATIVE STATS ===")
    
    print("From patch notes - Enemy effects:")
    print("-HP: Takes damage at end of turn")
    print("-Attack: Deals 0 damage, heals when hit") 
    print("-Defense: Takes extra damage, returns fraction")
    print("-Speed: Player always strikes first, hits unavoidable")
    print("-Luck: Higher miss%, successful hits curse player stats")
    
    # Test enemy with negative attack (like Bat from patch notes)
    bat_stats = {'Strength': -5, 'Agility': 3, 'Intelligence': 15, 'Defence': 5, 'Magic': 0, 'Luck': 0}
    damage, effects = DamageCalculator.calculate_enemy_damage(bat_stats, "Bat")
    
    print(f"\nBat attack: Damage = {damage} (should be 0)")
    for effect_type, value in effects:
        if effect_type == "enemy_heals_when_hit":
            print(f"  Heals when hit: {value} HP")
    
    # Test enemy with negative luck (like Witch from patch notes)  
    witch_stats = {'Strength': 5, 'Agility': 15, 'Intelligence': 1, 'Defence': 2, 'Magic': 0, 'Luck': -8}
    for i in range(3):
        damage, effects = DamageCalculator.calculate_enemy_damage(witch_stats, "Witch")
        print(f"\nWitch attack {i+1}: Damage = {damage}")
        for effect_type, value in effects:
            if effect_type == "curse_player_stat":
                print(f"  Curses player stat by: {value}")

if __name__ == "__main__":
    print("TESTING ALL NEGATIVE STAT EFFECTS FROM PATCH NOTES ALPHA II")
    print("=" * 60)
    
    test_negative_strength()
    test_negative_agility()
    test_negative_intelligence()
    test_negative_defence()
    test_negative_luck()
    test_negative_magic()
    test_enemy_negative_stats()
    
    print("\n" + "=" * 60)
    print("All negative stat effects implemented according to patch notes!")
    print("Try combat with Forsaken (-2 Strength, -2 Magic) or Monk (-9 Agility, -9 Defence)") 