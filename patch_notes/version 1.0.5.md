# PYRPG v 1.0.5:
## Charisma, choices, and quests that care!

> Taking off from version 1.0, we now can do some magical stuff!

### The road to 1.1:

This one got big. Like, bigger than the magic patch big. So instead of one giant drop, it comes out in stops, each one playable on its own. This is stop 1 of 4.

|Version|What's in it|
|---|---|
|1.0.5|Charisma, the quest board rework, Pirate, new items & enemies, and the other updates|
|1.0.6|Encounters: merchants, chests, mimics, cooks, sculptures (boons & curses), events, and Halt!|
|1.0.7|Unlocks, the Journal, and all the flavor text|
|1.1|Enemies with brains: the main event|

### what changed?

quite allot really:

- magic/spells
- spells and abilities learning
- difficulty curve balanced to be more satisfying with:
    - Better physical damage system, which brought all roles so far into the early game combat win percentages to 80+%. 
    - Better enemies difficulty encounters logic which goes up with in game depth.
    - Spell & ability damage separate from physical.
    - New damage type "searing" which bypasses every kind of defense/corruption.
- Allot more items and consumables
- New unique roles.
- spell/ability learning with level or by consumable usage.
- repeat loot now stacks instead of flooding your inventory space
- Almost all stats were reworked or heavily adjusted for the magic split.
- Fast travel to any depth reached with a gold cost.
- Quests moved to a CSV, with new quest types and perk rewards.
- Depth milestones: groups scale with depth, the 50+ enemy buff, and Death at 100+ (please don't ask xD)
- Mana: re-gen, potions, and full restore when resting in town.
- Defend rework: a real block that lasts until your next turn.


## introducing a new player stat:

I think it is prime time for charisma to be added. Well hello there handsome(s).

> - Charisma: shop costs are int(max(0,min(15,cha * 0.48)))% cheaper. 
>- You sway other people easier, giving you bonus odds, to not fail with sculptures , not encountering bad encounter types. +int(max(0,min(20, cha * 0.25)))% (on v1.0.6)
> - -Charisma: 
> - Benefit: You are so darn ugly, enemies intend to flee from you all the time (100% to 0% HP... lmao) but have more odds to drop stuff by min(45,abs(cha) * 1.5). (at v1.1) 
> - Debuff: You are so darn ugly..(I am sorry lol) that you sway others to make you fail (opposite odds and shop costs from +cha (up to +15% shop costs and up to +20% fail and bad encounters.)) (v 1.0.6)
>> charisma stat doesn't benefit combat damage, or encounter calculations
> - Anyone who charges you (merchants, cooks, guards...) is swayed too: costs like the cook's `1.5 ~ 2.3` slide to the cheap end the prettier you are, and to the pricey end the uglier.
> - Some encounters only happen at certain charisma. Behave (or don't) accordingly.
> - Old saves: your existing characters get their class's charisma value, no one starts at 0.


## here are some numbers! (charisma to roles):
|Class|Strength|Agility|Intelligence|**Charisma**|Defense|Magic|Luck|
|---|---|---|---|---|---|---|---|
|druid|4|4|6|**3**|4|6|4|
|dwarf|7|3|5|**1**|7|3|0|
|elf|4|7|6|**4**|7|5|2|
|forsaken|-1|5|3|**-7**|9|-4|4|
|mage|3|4|10|**2**|3|9|5|
|monk|5|5|8|**4**|-9|3|1|
|necromancer|1|4|6|**-5**|5|-8|5|
|ranger|3|11|6|**5**|2|2|9|
|rogue|5|9|5|**7**|4|2|9|
|satyr|2|7|9|**6**|3|4|4|
|tank|0|-5|2|**0**|12|1|5|
|warrior|6|4|4|**4**|6|3|1|

aren't the pretty? c:


## Raising/Lowering charisma:

> Per level changing charisma doesn't make logical sense, so, I will make quests mainly reward or lower your charisma based on actions.


## Quests rework:
The way old quests and quest board worked were dull and gave you each and every quest from the start.

So now here are the changes coming up:
- Quests opt in; choose whether to start any quest or not at your own pace.
- Quests progress: now each and any quest progress starts counting once one accepts it.
- Choice quests (or moral quests): Completing some quests may give you a choice to make which can be good, or bad. which will effect your charisma. (still completes them either case)
- Quest chains: Quests that open up after you do a prior quest, still experimental
- Quest enemies: some quests bring their own enemies with them (townsfolk, priests...), you fight them the moment you accept. Those enemies don't show up anywhere else.
- Some quests cost you charisma once they're done. Shady people make shady offers.


## new classes.
|Class|Strength|Agility|Intelligence|Charisma|Defense|Magic|Luck|
|---|---|---|---|---|---|---|---|
|Pirate|2|5|-8|-4|6|0|11|

> Pirate: not the sharpest cutlass in the chest, and nobody in town wants them at dinner, but boy are they lucky. The luckiest class in the game, tough as an old ship's hull, and magic? What's magic? Arr!


## Items (and small adjustments).
|Name|Consumable|Strength|Agility|Intelligence|**Charisma**|Defense|Magic|Luck|Rarity|Buyable|Droppable|
|------|-----|----|----|----|----|----|---|---|---|---|---|
|Arcane ring|No|0|0|3|**0**|2|5|0|32|Yes|Yes|
|Beam staff|No|0|0|3|**0**|0|3|1|12|Yes|No|
|Berserker armor|No|2|0|0|**-2**|4|0|0|1|Yes|No|
|Blade rush|Yes|0|0|0|**0**|0|0|0|22|Yes|No|
|Bloody crown|No|-6|2|9|**1**|-7|4|-1|6|No|Yes|
|Bomb|Yes|0|0|0|**0**|0|0|0|50|Yes|No|
|Cursed blade|No|6|0|0|**-1**|-3|0|-2|14|No|Yes|
|Dagger|No|1|3|0|**3**|0|0|1|30|Yes|Yes|
|Diamond sword|No|8|-3|0|**1**|2|1|3|15|Yes|Yes|
|Dice machine|Yes|0|0|0|**0**|0|0|0|20|Yes|No|
|Golden ring|No|0|0|0|**5**|2|0|5|32|No|Yes|
|Hard ring|No|0|0|0|**0**|7|0|0|32|Yes|Yes|
|Health potion|Yes|0|0|0|**0**|0|0|0|0|No|No|
|Hexing amulet|No|0|0|0|**0**|0|3|-9|10|No|Yes|
|Iron sword|No|4|1|0|**0**|1|0|2|30|Yes|No|
|Lucky clover|No|0|0|0|**2**|0|0|15|12|Yes|Yes|
|Magic mushroom|No|3|3|3|**3**|3|3|3|5|No|Yes|
|Mana potion|Yes|0|0|0|**0**|0|0|0|0|No|No|
|Mana rock|No|0|0|2|**0**|0|6|1|35|Yes|No|
|Mana rod|No|0|0|15|**0**|0|0|0|5|Yes|Yes|
|Mana surge book|Yes|0|0|0|**0**|0|0|0|0|No|No|
|Mind Shocker|No|10|5|-10|**-6**|4|0|4|7|No|Yes|
|Nature's codex|Yes|0|0|0|**0**|0|0|0|17|Yes|Yes|
|Necronomicon|No|0|0|10|**-4**|0|-10|2|10|~~Yes~~ → **No**|Yes|
|Nullifier|No|8|-5|-4|**-3**|-2|-1|0|9|No|Yes|
|Nuts|Yes|0|0|0|**0**|0|0|0|45|No|Yes|
|Power ring|No|5|0|0|**-1**|2|0|0|32|Yes|Yes|
|Scroll|No|0|0|7|**0**|0|3|0|25|Yes|Yes|
|Scroll of doom|Yes|0|0|0|**0**|0|0|0|0|No|No|
|Sleight of stats|No|0|0|0|**0**|0|0|0|6|Yes|No|
|Smart ring|No|0|0|5|**3**|2|0|0|32|Yes|Yes|
|Speed ring|No|0|5|0|**0**|2|0|0|32|Yes|Yes|
|Spiked gloves|No|6|-2|0|**-2**|0|0|2|22|Yes|Yes|
|Starter gear|No|1|1|1|**1**|1|1|1|60|Yes|No|
|Steel shield|No|0|-1|0|**2**|7|0|0|30|Yes|Yes|
|Swift coat|No|0|7|2|**6**|3|0|1|18|Yes|No|
|Thunder apprentice|Yes|0|0|0|**0**|0|0|0|25|Yes|No|
|Thunder disciple|Yes|0|0|0|**0**|0|0|0|0|No|No|
|Thunder master|Yes|0|0|0|**0**|0|0|0|0|No|No|
|Timer|Yes|0|0|0|**0**|0|0|0|15|Yes|No|
|Turtle shell|No|0|-7|2|**2**|12|0|0|14|Yes|No|
|Voodoo doll|No|2|0|3|**-3**|0|-1|-10|10|No|Yes|
|Voucher|Yes|0|0|0|**0**|0|0|0|15|No|Yes|
|Wooden sword|No|2|1|0|**0**|1|0|1|80|Yes|Yes|


## New items:
|Name|Consumable|Strength|Agility|Intelligence|Charisma|Defense|Magic|Luck|Rarity|Buyable|Droppable|
|------|-----|----|----|----|----|----|---|---|---|---|---|
|Big Bonk|No|15|-9|-5|0|2|0|0|5|No|Yes|
|Cutlass|No|3|3|0|1|0|0|6|13|No|Yes|
|Golden obol|No|0|0|3|8|1|0|8|4|No|Yes|
|Rapier|No|4|5|2|2|4|0|4|3|Yes|No|


## Some more enemies (some are special):
|Name|Corruption|HP|Attack|Defense|Speed|Luck|info|
|---|---|---|---|---|---|---|---|
|Mole|0|11|5|4|-5|0||
|Mole king|0|20|10|8|-20|0||
|Priest|0|25|-14|2|2|15|quest only| 
|Townfolk|0|15|3|1|2|0|quest only|
|Wisp|0|8|7|2|4|4||


## Other updates:
- Change player "Defence" to "Defense" (yes finally).
- Add ??? description.
- Better save & load data structure.
- Add csv.DictReader for better csv parsing.
- Fix the Charity and Spooky Area quests, which couldn't be completed before.
- Fix the quest voucher: it now goes to your loot and really gives 15% off. Old saves get theirs back.
- Quests now reward items.
- Quest system reworked: new quest types are easy to add
- Add more quests ([quests.csv](../data/quests.csv))
