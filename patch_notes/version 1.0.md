# PYRPG v 1.0:
## The age of magic....and abilities.... & knuckles?:

Welcome to PYRPG! or should I write welcome back?

Regarding Beta I, things are fully written, flows work overall, some edge parts are left, now onto a super big patch!

### what changed?:
- stats were adjusted and now feel overall balanced, well except for magic and int

- More enemies were added

- Encounters are based of off your stats x enemy stats

- EXP, gold, a shop, a town, only 1 quest available to do in town (will expand later)

- Enemies can appear in groups now, enemy group difficulty curve was a known issue, this patch provides several solutions to that!

- Fleeing an enemy and town returning

- rest odds and percentage healing.

- Loot & equipment

- Save deletions

- Auto-save opt-out

- Choosing which stat to raise on level-up

### **upcoming:**

Imagine this, you boot PYRPG, choose a magical class, you use "magic attack" in combat, and.... it's like you hit the enemy with a physical attack decorated as "magic". Plain as the day you were born.

### **NO MORE**
I am introducing, the age of magic and abilities & knuckles, splitting magic & physical damage. Pokemon gen 4 who?

anyhow, yeah:

- Add mana
- Add spells
- Add abilities
- AOE logic (both magic and abilities and consumables)
- More consumable items and ways to heal out of town and combat rather than being miserable in trying to rest
- Obviously add more quests
- No spells/abilities = spells/ability tab says it's empty, cry about it.
- Magical creatures (enemies & roles)
- Encounter difficulty curve rework (including groups)
- Implement "fast travel"
- Harsher death penalties

## enemies encounter:
Yes I know previous patch made it so enemies are encountered based on your stats, but I want the "depth" mechanic to contribute more towards what you may encounter.

> **encounter logic:**
>> - depth 1 ~ 5: encounter easier for you to defeat enemies (based on your stats * 0.25 ~ 0.75), group encounter odds 5%, for 2 enemies at once
>> - depth 6 ~ 10: encounter a mix of easy and somewhat tougher enemies. (self stats * 0.75 ~ 1.2) 8% groups, always of 2.
>> - depth 11 ~ 15: tougher to medium difficulty enemies (* 1.2 ~ 2). 15% groups 60% 2, 40% 3.
>> - depth 16 ~ 20: medium - hard (* 2 ~ 2.5). 25% groups, 55% 2, 45% 3.
>> - 21 ~ 50:  hard - insane (* 2.5 ~ 3.5). min(50,35 + (depth - 21))%  groups, 40% 2, 60% 3. 
>> - 50+... somehow?: enemies > 0 stats get buffed for depth - 50.
>> - 100+?: `min(100, depth - 99)%` Death is coming for you...you can't flee it.


## fast travel:
Reached a specific depth and got stuck or somehow died and returned to town? Well cry no more! "fast travel" option will take you up to the depth you reached for a price * depth number! (choose whichever <= depth)

fast travel cost: `int(5 * depth * 0.5)`

--------------



# *magic reworked:*

<a id="spell_damage"></a>
> ### Spell damage: 
> `Spell Base Damage × max(0.1, 1 + Magic × 0.1)`. A dedicated caster (high Magic) roughly doubles a spell's base damage. The multiplier is floored at 0.1 (10% of base) so damage can never hit 0 or go negative, no matter how far Magic gets pushed down via leveling.

> Three pools:
>> - Normal spells: learned by +Magic characters. -Magic can learn them too, but they're weaker, since the spell damage formula works against a negative Magic stat (see [Spell damage](#spell_damage)).
>> - Cursed spells: exclusive to -Magic (full power, part of their kit). Normal Magic characters never get access to them.
>> - Abilities: can be learned by anyone. Ability damage is separate from spell damage (spell damage boosts don't apply), each ability lists its own damage formula, and abilities cost mana too. Mana logic is coming up.

> **No spell/ability learned?** 
>> Selecting spells/abilities with nothing learned shows "you have no spells or abilities" and returns you back to choose a different action (Physical Attack, etc.) instead. doesn't waste the turn on an empty action.

> **mana:**
>> going forward mana pool is buffed by abs(intel). `mana = max(20, abs(intel) * 4.5)`.

> **-intelligence?:**
>> *adding AOE and hitting a different enemy doesn't make the debuff logical... reworking it!*
>>> Also adjusting -intel to be more powerful for heavier spell users:
>> - -intelligence: Debuff: `min(35, abs(intel) + 5)%` ~~chance to attack a different enemy~~ → **chance to waste `(spell/ability mana cost * 1.5)`** if spell/ability cost * 1.5 > your mana pool, spend all mana, this doesn't make the spell/ability fail. Benefit: ~~You find enemies weak points faster dealing~~ → **spells (spells only) deal** `int(0.5 * spell_damage) + int(min(abs(intel) // 3, abs(mag) * 0.8))` bonus **magic** damage **regardless if the debuff applied or not**.

> **-magic?:** 
>> for my next magic (heh get it, magic?) trick what if I told you it was thought of ahead of time... somewhat.
>> - -magic: Debuff: gain 15% less EXP. ~~Magic attacks~~ → **cursed spells** ~~drain `min(25, abs(-mag))%` from your MAX HP~~ → cost `min(abs(mag), mana_cost * 0.88)` HP **instead of mana**, Benefit: **Each ~~magic attack~~ → cursed spell has** `min(65, int(sqrt(abs(-mag)) * 10))%` chance to lower a **randomly picked** enemy stat by `min(7, abs(-mag))` 
>> - **additionally (and obviously) -mag only can access cursed spells, and deal less damage with normal spells (read [Spell damage](#spell_damage)). cursed spells deal `Spell Base Damage × max(0.1, 1 + abs(Magic) × 0.1)`**
>>> Having -int and -mag both means if you use a cursed spell, have `min(35, abs(intel) + 5)%` chance to cost `min(abs(mag), mana_cost * 0.88)` * 1.5 HP. or if you don't have the hp to pay. well, you die :D

> **-strength:**
>> strength curse shouldn't benefit or be damaged by spells
>>> Debuff: ~~After attacking~~ → using physical attacks or abilities, ~~damages~~ → **sears** you for ~~`abs(str) + int(max_hp * 0.01)`~~ → `int(abs(str) + int(min(max_hp *  0.08, abs(str)) * 0.5))` damage, **whether  you hit or miss the attack/ability**. Benefit: ~~hitting~~ → landing physical attacks or abilities on enemies heals you for  `min((abs(str) + missing_hp) * 0.8, (damage_done + abs(str)) * 0.65)`
>>>> *searing damage = damage that cannot be blocked or reduced.*

> **Player Defence:**
>> Defence had a hidden logic to damage reduction until now, which at +8 points you take 80% less damage, that is pretty crazy! This is a whole new property so this is also a defence rework:

>> def: You take `min(25,  2 + def * 0.7)%` less damage as long as your defence is > 0. at 0 and <= 0 defence, you get 0% damage reduction.
>>> choosing to defend in combat, you take `def% + min(10, max(0,def * 0.75))` damage ignorance. this doesn't have any effect vs sear.


> **Enemy Defense:**
>> Same as players defence, 8 points gave enemies 80% damage reduction quietly.
>> Enemy defense: take `min(20, 2 + def * 0.9)%` less physical damage, 
>> take `min(15, 1 + def * 0.2)%` less magic damage
>>> -def and def 0 have 0% damage defence!
>>> Damage reductions do not affect corruption

> **Enemy -defense:**
>>Enemies -defense is pretty satisfying, yet physical & magic split should treat them as well, adjustments:

>> -Defense: 
>> - The enemy takes `+max(3, abs(def) * 0.75)` bonus damage from **physical** attacks and  abilities, but will return ~~`min(5, (damage_taken + abs(def)) * 0.2)%`~~ →  **`min(11, abs(def) * 0.4)%`** of the flat damage taken back. 
>> - **Also, take `+max(7, abs(def) * 0.82)` bonus damage from spells, doesn't reflect any damage taken back.**

> **corruption:**
>> A nerf-rework feels at place.
>>> **Corruption replaces defense.** Corrupted enemies (corr > 0) ignore their defense stat entirely, positive *or* negative: no damage reduction, no -def bonus damage, no reflect. Corruption is their only protection.
>>>
>>> - **End of the enemy's turn:** takes ~~`max(current_hp * 0.08, max(corr, 5))`~~ → `max(current_hp * 0.04, corr, 3)` *searing* damage, then **corr grows by 1**.
>>> - **When you hit it:** your damage is reduced by corr, the enemy takes `damage_taken - corr` *searing* damage.
>>> - **Hit too weak?** If `damage_taken - corr <= 0`, the enemy heals instead: ~~`min(max_hp * 0.01, (damage_taken + corr) * 0.03)`~~ → `min(corr * 0.75, abs(damage_taken - corr))`.
>>>> *searing damage = damage that cannot be blocked or reduced.*


## physical damage:
> physical damage formula feels too good for certain combatant win rates (cough, warriors, rogues and rangers) so, I feel like a roles should benefiet from all none magical stats.
>> Physical damage calculation: int(sqrt(abs(Str) + abs(Agi) + abs(Lck) + abs(Def) + 15) * 2.2)

## learning spells/abilities:
> I will add new consumable loot drops/shop items (like TMs) that teach you spells and abilities, natural level up spell learning (again... pokemon who?), and give some roles starting spells (looking at you mages and necros).

## mana generation:
> resting successfully gives up to 30% of max mana back, natural per turn 10% of max mana regeneration, mana potions (consumable to be added to shop) that fill you with 20 mana (or fill to full if max mana <= 20.... somehow).
>> Resting in town fully restores mana, same as HP. Mana carries over between fights; it doesn't reset per combat. Same as HP.

## items:
> Adding the new items also means that I will make it so the healing/spell learning (and probably future consumables) can be used out of combat.


## new enemies:

> I know that more on the easier side enemies need to be added, so I will add some according to the magical patch theme, while also adding other power level enemies too.

|name|corr|hp|attack|def|speed|luck|
|----|----|----|----|----|----|----|
|Banshee|0|13|8|2|0|-12|
|Death|0|9999|9999|9999|9999|-9999|
|Elf|0|13|8|0|11|7|
|Fairy|0|12|3|11|25|7|
|Living armor|0|200|2|100|0|0|
|Unicorn|0|20|8|2|15|10|
|Vampire|0|9|-15|2|6|0|
|Weakling|0|12|2|2|1|1|
|Werewolf|1|23|13|0|20|4|


## enemies adjustment:

|name|corr|hp|atk|def|spd|lck|
|----|----|----|----|----|----|----|
|Cursed Human|15|40|9|~~-5~~ → 0|10|-5|
|Jester|20|35|4|~~10~~ → 0|15|22|
|Plague Rat|~~12~~ → 0|10|~~5~~ → 2 |~~2~~ → 3|~~15~~ → 10|-6|
|Zombie|8|20|3|~~-10~~ → 0|-2|-2|

## new roles:

> Some new roles as well, mostly fitting the theme.
>>The thought line is to expand the amount of choices, so some may hit similar stat lines or be tuned in the future.

|Cls|Str|Agi|Intel|Def|Mag|Lck|
|----|----|----|----|----|----|----|
|Dwarf|7|3|5|7|3|0|
|Elf|4|7|6|4|5|2|
|Satyr|2|7|9|3|4|4|
|Tank|0|-5|2|12|1|5|

## role buffs:

> - **forsaken:** The forsaken class is the weakest of the bunch, while making them a double edged sword was the intended route, their play routh feels more like a shattering glass. buffing forsaken to see the combat win rate raising.
>> forsaken stats: ~~-2,3,2,10,-2,2~~ → -1,5,3,9,-4,4
> - **Necromancer:** While necros sit high... or should I say low? on -mag getting strong magic attacks this patch, their overall stats however need a little touch up.
>> Necromancer stats: ~~1,2,6,4,-8,5~~ → 1,4,6,5,-8,5

## role nerfs:
> - **Druid:** Druids combat win rates are the high currently, sitting at 90~% early on, while it is satisfying, they could become lower.
>> Druid stats: ~~4,5,7,5,8,6~~ → 4,4,6,4,6,4
> - **Warrior:** Warriors are one of the strongest roles (2nd to rangers) on the earlier game, I do want their stats to dish out less power.
>> Warrior stats: ~~9,5,3,8,2,4~~ → 6,4,4,6,3,1

## new items:

- Beam staff: equipment, 0,0,3,0,3,1, special equipment passive: While equipped; spell "hyper beam" enters your spells/abilities tab automatically, spell mana cost: 100% of your mana, spell base damage: `int(max(5, mana * 0.40))`, can be cast once a combat. single target, rarity 12, purchase-able
- Berserker's armor: equipment, 2,0,0,4,0,0, equipment passive: when you take a hit that would lower your HP to half while in combat, each turn; gain 1 strength, until the combat ends. resets when combat ends. undroppable, rarity 1, purchasable, healing to > half HP stops the passive too.
- Blade rush: consumable, on usage, learn blade rush ability, 22 mana cost, for 4 turns deal `max(4, int(str * 0.8 + abs(mag) * 0.4))` physical AOE damage, you cannot make any other actions during those 4 turns. rarity 22, undroppable, purchaseable.
- Diamond sword: equipment, 8,-3,0,2,1,3,15,yes,yes.
- Health potion: consumable, upon usage, heal for 20 HP, costs 15 gold, always available and doesn't go out of stock.
- Mana potion: consumable, upon usage, gain 20 mana, costs 15 gold, always available and doesn't go out of stock.
- Mana rod: equipment, 0,0,15,0,0,0, rarity: 5. buyable droppable
- Mana surge book: consumable, on use learn the spell mana surge, spell mana; 5, +3 each cast in combat, spell damage: 2, +2 each cast in combat. undroppable, not purchase-able, mages start with this consumable in their inventory.
- Nature's codex: consumable, on use learn the ability nature's gift, 25 mana, ability effect: for 3 turns heal 5 HP. Monks start out with this in their inventory, 17 rarity, droppable, purchaseable
- Scroll of doom: consumable, upon usage learn the cursed spell 'DOOM', spell base damage: 10, single target, costs 8 mana, necros start with the consumable in their inventory.
- Sleight of stats: equippable, 0,0,0,0,0,0, special passive: each time you win 3 combats, raise one random stat by 1, max 10 each permanently. undroppable, purchaseable, rarity 6.
- Thunder apprentice: consumable in combat, once per combat,on usage, call an AOE lightning that deals 6 damage. non droppable, rarity 25 purchase-able. Special consumable quest; use Thunder apprentice 6 times, becomes to Thunder disciple.
- Thunder disciple: consumable in combat, once per combat, on usage, call an AOE thunder that deal 12 damage, non droppable, 0 rarity, not purchase-able. Special consumable quest; use Thunder disciple 6 times, becomes to Thunder master.
- Thunder master: consumable in combat, once per combat, on usage, call an AOE storm that deal 18 damage, non droppable, 0 rarity, not purchase-able.
- Wooden sword: equipment, 2,1,0,1,0,1,80,yes,yes.


## other spells & abilities:
- Arrowshot: ability, 5 mana, shoot a magical arrow on an enemy, dealing int((agi * 0.7 + abs(mag) * 0.3)) magic damage. rangers start with that.
- Backstab: ability, 11 mana, teleport behind an enemmie's back and stab it, dealing int(15 + agi * 0.8) searing damage. Rogue learn this at level 5. 
- Blade bonk: ability, 5 mana, bonk an enemy with your weapon, deal int(5 + str * 0.55) damage. Warriors learn this ability at level 2.
- Cursed strike: cursed spell, 3 mana, strike an enemy with your cursed soul for 5 spell damage. Forsakens start with that.
- Ice shower: Spell, 20 mana, summon a shower of sharp ice from the sky, dealing AOE 9 spell damage. Mages learn this at level 3.
- Light shock: Spell, 12 mana, shock an enemy for 8 spell damage, elves learn that at level 2.
- Dark shock: Cursed spell, 2 mana, shock an enemy for 6 spell damage, necros learn that at level 2.
- Lava bomb: Spell, 22 mana, throw a lava boulder at an enemy, deal 12 spell damage, the boulder explodes and deals extra 5 AOE spell damage. Druids learn this at level 3.
- Berserk scream: Ability, 15 mana, one use per combat. Go berserk with a scream, raise you strength by int(max_hp * 0.20) but lower your intellect by int(max_hp * 0.20), this ability can make intellect reach < 0 numbers. your stats reset at combat's end. Dwarves learn this at level 4.

## items adjustment (and filling out last patch added ones):

> - Bomb
>> AOE damage... yeah, but also I didn't really note what it does last patch... oops.
>>> **bomb:** consumable buyable undroppable, 50 rarity. on usage deal 35 damage to all enemies. can be used once, disappears on usage.

>  - **Dice machine:**
>> dice machine as a whole felt like its identity isn't correct for it, reworking into a true consumable and placed its old usage/equippable instance into Sleight of stats:
>>> **dice machine:** consumable 6 times per combat, on use, roll a 6 sided dice, summon a huge dice that deals AOE dice damage. rarity ~~3~~ → 20

> - Timer
>> having an extra turn for yourself in combat is pretty exciting, but I am dropping its stats to become a full on consumable and some small nerfs. (this was also hidden last patch).
>>> **Timer:** consumable undroppable purchaseable, ~~25~~ → 15 rarity.
>>> On use, gain another turn, after that turn cooldown for ~~5~~ → 6 turns.

> - Voucher
>> this was hidden last patch.
>>> consumable, droppable, unpurchasable. passive: your next shop purchase costs 15% less, upon purchasing, this gets consumed/disappears.

- all rings: giving all rings extra 2 def, and giving arcane ring more purpose.
- sword evolution: making things a little minecraft-y... but also real life accurate kinda? with the addition of wooden and diamond swords.



|Name|Consumable|Strength|Agility|Intelligence|Defence|Magic|Luck|Rarity|Buyable|Droppable|
|-|-|-|-|-|-|-|-|-|-|-|
|Arcane Ring|No|0|0|~~0~~ → 3|~~0~~ → 2|5|0|~~35~~ → 32 |Yes|Yes|
|Bloody Crown|No|-6|2|9|-7|4|-1|6|No|Yes|
|Bomb|Yes|0|0|0|0|0|0|50|Yes|No|
|Cursed Blade|No|6|0|0|-3|0|-2|14|No|Yes|
|Dagger|No|1|~~4~~ → 3|0|0|0|1|~~20~~ → 30|Yes|Yes|
|Dice machine|Yes|0|0|0|0|0|0|~~3~~ → 20|~~No~~ → Yes|No|
|Golden Ring|No|0|0|0|~~0~~ → 2|0|5|~~35~~ → 32|No|Yes|
|Hard Ring|No|0|0|0|~~5~~ → 7|0|0|~~35~~ → 32|Yes|Yes|
|Hexing amulet|No|0|0|0|0|3|-9|10|No|Yes|
|Iron Sword|No|~~3~~ → 4|1|0|~~0~~ → 1|0|~~4~~ → 2|30|Yes|No|
|Lucky Clover|No|0|0|0|0|0|15|12|Yes|Yes|
|Magic Mushroom|No|3|3|3|3|3|3|5|No|Yes|
|Mana rock|No|0|0|2|0|6|1|35|Yes|No|
|Mind Shocker|No|10|5|-10|4|0|4|7|No|Yes|
|Necronomicon|No|0|0|10|0|-10|2|10|Yes|Yes|
|Nullifier|No|8|-4|-3|-2|-1|0|9|No|Yes|
|Power Ring|No|5|0|0|2|0|0|~~35~~ → 32|Yes|Yes|
|Scroll|No|0|0|7|0|3|0|25|Yes|Yes|
|Smart Ring|No|0|0|5|2|0|0|~~35~~ → 32|Yes|Yes|
|Speed Ring|No|0|5|0|2|0|0|~~35~~ → 32|Yes|Yes|
|Spiked Gloves|No|6|-2|0|0|0|2|22|Yes|Yes|
|Starter gear|No|1|1|1|1|1|1|60|Yes|No|
|Steel Shield|No|0|-1|0|7|0|0|30|Yes|Yes|
|Swift coat|No|0|7|2|3|0|1|18|Yes|No|
|Timer|Yes|0|~~7~~ → 0|~~1~~ → 0|0|0|0|~~25~~ → 15|Yes|No|
|Turtle Shell|No|0|-7|2|12|0|0|14|Yes|No|
|Voodoo Doll|No|2|0|3|0|-1|-10|10|No|Yes|
|Voucher|Yes|0|0|0|0|0|0|15|No|Yes|

### Shop adjustments: 
> adding a wooden sword with 80 rarity and shop costs depending on `(highest_rarity - rarity) * 0.79` made every price go up.... inflation isn't for today plus this doesn't make any sense as well.
>> shop costs: ~~(highest_rarity − rarity) × 0.79~~ → `max(15,int(abs(65 - rarity) * 0.65))`

### Quests:
> Beta patch, I added only one quest, and then forgot about it. This patch I am introducing a new data csv for quests, so make sure you follow it up, since writing every quest I add will be too long. c:

### Death penalties:
> So far, I didn't really want to touch dying consequences too badly since the game's specs were small and larger penalties would have felt unfair. Now that v1.0 is coming up some more consequences feel right. You'd probably miss pre beta days where dying just full healed you.
>> Dying in combat, loses you 15% of current gold, have a 25% chance for an item to be lost (aka be removed from inventory or equipment), resurrect with 30% mana based on max mana, and 50% HP based on max HP. lose 20% of your EXP progress (e.g. 60% → 48%, minimum 0%), can't drop a level. 

## miscellaneous updates:
- Sort roles alphabetically
- Sort descriptions alphabetically (by roles)
- Add new roles descriptions
- Fix inventory bug where 0 always unequips your equipment. (replaced by u).