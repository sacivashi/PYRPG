# PYRPG v 1.1:
## Enemies but with brains and different encounters!

> Taking off from version 1.0, we now can do some magical stuff!

### what changed?

quite allot really:

- magic/spells
- spells and abilities learning
- difficulty curve balanced to be more satisfying with:
    - Better physical damage system, which brought all roles so far into the early game combat win percentages to 80+%. 
    - Better enemies difficulty encounters logic which goes up with in game depth.
    - Spell & ability damage seperate from physical.
    - New damage type "searing" which bypasses every kind of defense/defence/corruption.
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
- Sculptures (or boons): Can be "encountered", at depth 5+, prayer sculptures which can be one of the following (will tell you by text):
    - Of resting: better rest odd for three time (+15%)
    - Of survival: higher rest heal for three time (only on success).
    - Of Prosperity: Some more gold income (+12% on next win)
    - Of Intellect: A boost of exp (+30% on next win)
    - Of Growth: Set your max_HP to +15 and then full heal, that max hp stays on till you win combat.
    - Of fear: Entering combat, your charisma* stat is multiplied by -1, clears at combat's end.


    Any of those sculptures have a chance to fail.. The gods have their own reasons.
- Random event(s): Can be "encountered", giving you a choice to proceed by... choose cautiously.
- Changing "enemies.csv" into "encounters.csv" and having a new "type" value.

And now for the main event:

## enemies move logic:

Following the solutions enemies encountered now have their nuggings installed to them:

> enemy thought process:
>> - on 100% ~ 80% of HP, priorities dishing out attacks
>>> New attack types:
>>> - Charge attack: the enemy prepares a large scale attack, takes the enemy a turn to charge up, but damages player for (enemy attack * 1.5) damage
>>> - Charge attack but you are a healer (-attack):  takes the enemy a turn to charge up, sears * 1.3 of siphon value (siphon value stays the same). charge attacks have a 25% chance to happen, and will prompt with "(enemy name) bides..." or "Enemy name is smiling wickedly"
>> - 80% ~ 45% of HP, choose between attempting to defend and attacking:
>>> 50/50 odds of attacking or defending; if defending and player physically attacks, enemy has a channce to counter attack
>>> - counter attack: The enemy strikes the player for attack value + a portion of defense value int(max(0,def * 0.45))
>> - 45% and less:
>>> Enemy will start thinking about fleeing, fleeing odds depend on it's speed + luck int(max(0,min(15,spd * 0.44 + lck * 0.44)))%, 40/50% attack/defend if failing. Enemy fleeing has 30% to drop some gold (3 ~ 8) or a loot, but woun't give exp.

## introducing a new player stat:

I think it is prime time for charisma to be added. Well hello there handsomes.

> - Charisma: shop costs are int(max(0,min(15,cha * 0.48)))% cheaper. You sway other people easier, giving you bonus odds, to not fail with sculptures, not encountring bad encounter types. +int(max(0,min(20, cha * 0.25)))%
> - -Charisma: 
> - Benefeit..?: You are so darn ugly, enemies intend to flee from you all the time (100 to 0% HP... lmao) but have more odds to drop stuff by min(45,abs(cha) * 1.5). 
> - Debuff: You are so darn ugly..(I am sorry lol) that you sway others to make you fail (opposite odds and shop costs from +cha (up to +15% shop costs and up to +20% fail and bad encounters.))
>> charisma stat doesn't benefit combat damage, or encounter calculations