"""
Example of how to use the new turn-based combat system
Run this file to test the combat mechanics
"""

from game_data.combat.combat import start_combat
from game_data.data_inputs.input_name.input_name import InputName

def test_combat():
    """Test the combat system with a player"""
    print("=== COMBAT SYSTEM TEST ===")
    
    # Get player data (either new or existing)
    player_data = InputName.input_name()
    
    # Start combat with a random enemy
    enemy_name = "orc"  # You can change this to any enemy from your CSV
    
    print(f"\nA wild {enemy_name} appears!")
    result = start_combat(player_data, enemy_name)
    
    if result == "victory":
        print("Congratulations! You won the battle!")
    elif result == "defeat":
        print("Better luck next time!")
    else:
        print("Combat ended unexpectedly.")

def combat_flow_explanation():
    """Explains how the turn system works"""
    print("""
=== TURN-BASED COMBAT FLOW ===

1. Initiative is calculated based on Agility stats
2. Higher initiative goes first
3. On your turn you can:
   - Attack: If you miss, your turn ends immediately
   - Defend: Reduces incoming damage for the enemy's next attack
   - Skip Turn: Immediately end your turn

4. When your turn ends (successful attack, miss, defend, or skip):
   - Control passes to the enemy
   - Enemy takes their action
   - Control returns to you

5. Combat continues until:
   - You defeat the enemy (enemy HP reaches 0)
   - You are defeated (your HP reaches 0)
   - Combat is manually ended

=== SPECIAL MECHANICS ===

- Negative stats have unique effects (see your patch notes)
- Missing attacks due to negative Strength causes self-damage
- Negative Luck makes attacks unavoidable when they hit
- Negative Defence increases incoming damage but reflects some back
- Defending gives temporary damage reduction for one turn

Try different combinations and see how your role's stats affect combat!
    """)

if __name__ == "__main__":
    combat_flow_explanation()
    
    choice = input("\nWould you like to test combat? (yes/no): ").strip().lower()
    if choice in ('yes', 'y'):
        test_combat()
    else:
        print("Thanks for reading! You can import start_combat() to use in your main game.") 