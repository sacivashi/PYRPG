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
- Wandering merchant(s): Can be "encountered" by depth 11+, they sell you items for `(base store cost * 1.3)` the cost, but have a chance to have rarer unpurchaseable loot on them `(still cost * 1.3)`. They also accept to take loot for `int(item_rarity * 0.4)` gold back.
- Thief merchant: Same as merchant but buying or selling from/to them makes them suprise attack you (which means, the intiation will be theirs regardless). selling an item + winning combat returns you the item.