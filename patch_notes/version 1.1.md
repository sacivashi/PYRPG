# PYRPG v 1.1:
## Enemies but with brains and different encounters!

> Taking off from version 1.0, we now can do some magical stuff!

### what changed?

quite allot really:

- magic/spells
- spells and abilities learning
- difficulty curve balanced to be more satisfying with:
- - Better physical damage system, which brought all roles so far into the early game combat win percentages to 80+%. 
- - Better enemies difficulty encounters logic which goes up with in game depth.
- - Spell & ability damage seperate from physical.
- - New damage type "searing" which bypasses every kind of defense/defence/corruption.
- Allot more items and consumables
- New unique roles.
- spell/ability learning with level or by consumable usage.
- repeat loot now stacks instead of flooding your inventory space
- Almost all stats were reworked or heavily adjusted for the magic split.
- Fast travel to any depth reached with a gold cost.
- Quests moved to a CSV, with new quest types and perk rewards.
- Depth milestones: groups scale with depth, the 50+ enemy buff, and Death at 100+ (please don't ask xD)
- Mana: regen, potions, and full restore when resting in town.
- Defend rework: a real block that lasts until your next turn.

## re-touching enemies... not in a weird way you freaks!

Lets face it, enemies are quite boring, you encounter one (or two or three) and all they ever do is; attack you, or attack the moment they have the opportunity.

This enemy's behaviour dishes out few problems:

1. It gives the player an aggressive behaviour restriction as well, a "kill or die" sort of system.
2. It makes the game be mostly a "sit there and spam number 1 till enemy dies" game... which becomes hectic and boring (from tests too it feels like so). 
3. Enemies have no... flavor, each enemy is like the last one all that matter are the stats, a name doesn't make something unique if it acts similarly.

### The fixes:
Adding some more encounters rather than just enemies:
- Wandering merchant(s): Can be "encountered" by depth 11+, they sell you items for `(base store cost * 1.3)` the cost, but have a chance to have rarer unpurchaseable loot on them `(still cost * 1.3)`. They also accept to take loot for `int(35% of item's price)` sell value. Has a chance to be thief merchant.
- Thief merchant(s): Same as merchant but buying or selling from/to them makes them suprise attack you (which means, the intiation will be theirs regardless). selling an item + winning combat returns you the item. Buying and winning returns you the gold you wasted, but no item (unless a loot dropped magically). theif merchants aren't called thief merchants, are called merchants. same stats as normal enemy thief.
- Treasure chest(s): Can be "encountered", at any depth, contain some gold (5 ~ 13) and may contain a random loot. Has a chance to be a mimic
- Mimic chest(s): Same as treasure, but choosing to open these makes them surprise attack you, defeating one gives you bonus gold (3 ~ 11). mimics aren't called mimics, just treasure chest.
- Healer(s): (debating to call those cooks) Can be "encountered" at depth 5+, pay int(choosen_hp value * 2.3) and heal that value.