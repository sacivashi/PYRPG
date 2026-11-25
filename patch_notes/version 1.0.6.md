# PYRPG v 1.0.6:
## Different encounters!

> Taking off from version 1.0.5, the dungeon finally has more in it than things that want you dead.

### The road to 1.1:

This one got big. Like, bigger than the magic patch big. So instead of one giant drop, it comes out in stops, each one playable on its own. This is stop 2 of 4.

|Version|What's in it|
|---|---|
|1.0.5|Charisma, the quest board rework, Pirate, new items & enemies, and the other updates|
|1.0.6|Encounters: merchants, chests, mimics, cooks, sculptures (boons & curses), events, and Halt!|
|1.0.7|Unlocks, the Journal, and all the flavor text|
|1.1|Enemies with brains: the main event|

### what changed?

last stop (1.0.5):

- Charisma, a brand new stat (hello there handsomes).
- Quest board rework: opt-in quests, moral choices, quest chains, quest-only enemies.
- Pirate, new items, new enemies.


## re-touching enemies... not in a weird way you freaks!

Lets face it, enemies are quite boring, you encounter one (or two or three) and all they ever do is; attack you, or attack the moment they have the opportunity.

This enemy's behavior dishes out few problems:

1. It gives the player an aggressive behavior restriction as well, a "kill or die" sort of system.
2. It makes the game be mostly a "sit there and spam number 1 till enemy dies" game... which becomes hectic and boring (from tests too it feels like so). 
3. Enemies have no... flavor, each enemy is like the last one all that matter are the stats, a name doesn't make something unique if it acts similarly.

### The fixes:
- Have a 25% chance to get a passive encounter when you press explore.
- Add new "encounters.csv"
Adding some more encounters rather than just enemies:
- Wandering merchant(s)(25% rate): Can be "encountered" by depth 11+, they sell you items for `(base store cost * 1.3)` the cost, but have a chance to have rarer unpurchaseable loot on them `(still cost * 1.3)`. They also accept to take loot for `int(35% of item's price)` sell value. Has a chance to be thief merchant.
- Thief merchant(s) (11% rate): Same as merchant but buying or selling from/to them makes them suprise attack you (which means, the intiation will be theirs regardless). selling an item + winning combat returns you the item. Buying and winning returns you the gold you wasted, but no item (unless a loot dropped magically). thief merchants aren't called thief merchants, are called merchants. same stats as normal enemy thief.
- Treasure chest(s) (25% rate): Can be "encountered", at any depth, contain some gold (5 ~ 13) and may contain a random loot. Has a chance to be a mimic. **Chests in encounter adventures are always good**
- Mimic chest(s) (5% rate): Same as treasure, but choosing to open these makes them surprise attack you, defeating one gives you bonus gold (3 ~ 11). mimics aren't called mimics, just treasure chest.
- Cook(s) (22% rate): Can be "encountered" at depth 5+, pay int(chosen_hp value * 1.5 ~ 2.3 depending on cha) and heal that value.
> Sculptures (or boons & curses) (12% rate): Can be "encountered", at depth 5+, prayer sculptures which can be one of the following (the effect is told after usage):
>
    Of resting: better rest odd for three time (+15%)
    Of survival: higher rest heal for three time (only on success) (+15% of max HP & mana, so 45% per rest).
    Of Prosperity: Some more gold income (+12% on next win)
    Of Intellect: A boost of exp (+30% on next win)
    Of Growth: Set your max_HP to +15 and then full heal, that max hp stays on till you win combat.
    Of fear: Lower your charisma by 999. effects for 5 encounters.
    Of Crippling: Change your strength to 0. effects on till a successful rest.
    Of misery: Change your luck to 0. effects on till a successful rest.


    Any of those sculptures have a 10% chance to fail.. The gods have their own reasons.
- Random event(s)/ adventure(s) (several rates, look at encounters csv): Can be "encountered" at several depths, giving you a choice to proceed by... choose cautiously.. A little taste of what's out there:
    - Cave entrance: something lives in there. Two somethings, actually.
    - A strange obelisk: free EXP? Nothing is free...
    - Graveyard: the dead don't stay down around here.
    - Sudden Hunger: only when you're at half HP or less. You find something to eat... and it's alive.
- Halt! (town event, 5% rate): Did something you shouldn't have? While your charisma is below 0, a guard may stop you on your way back to town. Pay a fine (15 ~ 40 gold, the better your charisma the cheaper), or refuse and fight. Lose the fight and the guard takes the full 40 anyway (or everything you've got, if you're that broke).


## Some more:

So yeah, there are bad passive encounters. But no worries, your brain can sometimes tell these encounters, if they are indeed bad.

> Have a int(max(0,min(45,intel * 1.7)))% chance to notice bad passive encounter.

- Noticing flavor(s):
> thief merchant:

    "This merchant seems cheeky to me.."
    "I got that gut feeling I shouldn't trust this one."
    "This merchant's eyes seem to glint towards my pockets..."
    "I feel malicious intent.."
    "I don't like this one's face."
    "Maybe, better not."
    "With a squint of an eye, looks suspicious"

> Mimic:
        
    "I think I just seen it lick its lid."
    "I can hear a heartbeat."
    "This chest has a soul to it, I know it."
    "I know a Mimic when I see it!"
    "This one, don't open it."
    "Oh believe me this chest has no gold or items..."

> Bad failed to notice or fine passive encounter flavor(s) (25%):
>
    "Seems fine to me."
    "Let's have a gander."
    "Looks okay."
    "Please be fine."
    "Something with the script tells me, this one is good."

> Not hitting any of those flavors:

    Passive encounters choices:
    "As you walk by there seem to be a (chest/merchant), (flavor if hit it). {do you open it? y\n} or {buy\sell\leave}."

## Abilities:
Rum: Self heal & nerf ability, once per combat, on use: heal `max(5,(min(abs(lck) * 0.95, 15)))` HP, but lower you intellect by max(8,abs(intel)) for the rest of combat.
Flintlock: once per combat, on use deal: `18 + ((abs(lck) + abs(agi)) * 0.85)` physical damage. special ability passive; landing this ability has a `abs(lck) * 0.8%` chance to add `max(3,(min(abs(lck) * 0.8,12)))` gold reward vs an enemy. Pirates learn (to shoot) this at level 3, yes they bring guns to a sword fight sort of speak.


## Mimic added:

|Name|Corruption|HP|Attack|Defense|Speed|Luck|
|---|---|---|---|---|---|---|
|Mimic|0|20|5|8|12|0|
> Mimic > 0 stats get stronger the deeper you are by `(base stats + depth - 1)`, past depth 50 buff are also included. Enemy encounter calculations do not affect Mimics.
>> Same goes for thief merchant, only if it is a thief merchant


## New items:
|Name|Consumable|Strength|Agility|Intelligence|Charisma|Defense|Magic|Luck|Rarity|Buyable|Droppable|
|------|-----|----|----|----|----|----|---|---|---|---|---|
|Prayer card|Yes|0|0|0|0|0|0|0|28|Yes|No|

Prayer card: only out of combat, on use receive a random prayer or curse boon


## New enemies:
|Name|Corruption|HP|Attack|Defense|Speed|Luck|info|
|---|---|---|---|---|---|---|---|
|Guard|0|100|12|22|8|0|event only|
