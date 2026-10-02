# PYRPG v 1.0 & knuckles:
## The age of magic....and abilities.... & knuckles?:

Welcome to PYRPG! or should I write welcome back?

Regarding Beta I, things are fully written, flows work overall, some edge parts are left, now onto a super big patch! & knuckles

### what changed?:
- stats were adjusted and now feel overall balanced, well except for magic and int

- More enemies were added

- Encounters are based of off your stats x enemy stats

- EXP, gold, a shop, a town, only 1 quest available to do in town (will expand later)

- Enemies can appear in groups now, enemy group difficulty curve is a known issue, I am thinking on solutions while writing this patch...

- Fleeing an enemy and town returning

- rest odds and percentage healing.

- Loot & equipment

- Save deletions

- Auto-save opt-out

- Choosing which stat to raise on level-up

### **upcoming:**

Imagine this, you boot PYRPG, choose a magical class, you use "magic attack" in combat, and.... it's like you hit the enemy with a physical attack decorated as "magic". Plain as the day you were born.

### **NO MORE**
I am introducing, the age of magic and abilities & knuckles, splitting magic & physical damage. Pokemon gen 3 who?

anyhow, yeah:

- Add mana
- Add spells
- Add abilities
- AOE logic (both magic and abilities and consumables)
- More consumable items and ways to heal out of town and combat rather than being misrable in trying to rest
- Obviously add more quests
- No spells = no magic attacks, cry about it.
- DOT spells/attacks?
- Magical creatures (enemies & roles)

## stats and logic:

*magic reworked:*

> **Spell damage:** `Spell Base Damage × max(0.1, 1 + Magic × 0.1)`. A dedicated caster (high Magic) roughly doubles a spell's base damage. The multiplier is floored at 0.1 (10% of base) so damage can never hit 0 or go negative, no matter how far Magic gets pushed down via leveling.

> **Two spell pools:** `+Magic` learns from the normal abilities list. `-Magic` gets their own exclusive **cursed spells** (full power, part of their kit) *and* can also learn from the normal list — just weaker there, since the floor formula above works against a negative Magic stat. Cursed spells stay exclusive to `-Magic`; normal-Magic characters never get access to them.

> **No spell/abilty learned?** Selecting abilities with nothing learned shows "you have no spells" and kicks you back to choose a different action (Physical Attack, etc.) instead — doesn't waste the turn on an empty action.

> **-intelligence?:**
>> *adding AOE and hitting a different enemy doesn't make the debuff logical... reworking it!*
>> - going forward mana pool is buffed by abs(int). `mana = max(20, abs(int) * 1.1)`. Also adjusting -int to be more powerful for heavier spells users:
>> - -intelligence: Debuff: `min(35, abs(-int) + 5)%` ~~chance to attack a different enemy~~ → **chance to waste `(spell mana cost * 1.5)`** Benefit: ~~You find enemies weak points faster dealing~~ → **your spells deal** `int(0.08 * damage) + int(min(abs(-int) * 0.75, max(abs(magic), 0) // 8))` bonus **magic** damage **regardless if the debuff applied or not**.

> **-magic?:** 
>> for my next magic (heh get it, magic?) trick what if I told you it was thought of ahead of time... somewhat?
>> - -magic: Debuff: ~~Magic attacks~~ → **cursed spells** ~~drain `min(25, abs(-mag))%` from your MAX HP~~ → cost min(abs(mag), mana_cost * 0.88) HP **instead of mana**, and get 15% less EXP. Benefit: **Each ~~magic attack~~ → cursed spell has** `min(65, int(sqrt(abs(-mag)) * 10))%` chance to lower a **randomly picked** enemy stat by `min(7, abs(-mag))` 
>> - **additionally (and obviously) -mag only can access cursed spells, and deal less damage with normal spells (read line 50). cursed spells deal `Spell Base Damage × max(0.1, 1 + abs(Magic) × 0.1)`**

> **-strength:**
>> strength curse shouldn't benefit or be damaged by spells
>> Debuff: ~~After attacking~~ → using physical attacks or abilities, damages you for ~~`abs(str) + int(max_hp * 0.01)`~~ → `int(abs(str) + int(**min**(max_hp * ~~0.01~~ → 0.08, **abs(str)) * 0.7**))` damage, **whether  you hit or miss the attack**. Benefit: ~~hitting~~ → landing physical attacks or abilities on enemies heals you for  `min(int(sqrt(missing_hp + damage_done) * 0.5), int(self_damage * 0.75))`

> **Player Defence:**
>> Defence had a hidden logic to damage reduction until now, which at +8 points you take 80% less damage, that is pretty crazy! This is a whole new property so this is also a defence rework:

>> def: You take `min(25, 1 + def * 0.9)%` less damage

> **Enemy Defense:**
>> Same as players defence, 8 points gave enemies 80% damage reduction quietly.

>> Enemy defense: take `min(20, 2 + def * 0.6)%` less physical damage, 

>> take `min(15, 1 + def * 0.2)%` less magic damage

> **Enemy -defense:**
>>Enemies -defense is pretty satisfying, yet physical & magic split should treat them as well, adjustments:

>> -Defense: The enemy takes `+max(3, abs(-def) * 0.75)` bonus damage from **physical** attacks and  abilities, but will return ~~`min(5, (damage_taken + abs(-def)) * 0.2)%`~~ →  **`min(11, abs(def) * 0.4)%`** of flat damage back. 
**Also, take `max(7, abs(-def) * 0.82)` bonus damage from spells, doesn't reflect any damage back.**

> **corruption:**
>> A nerf-rework feels at place.
>>> Corruption: The enemy ~~recieves~~ → takes  ~~`max(current_hp * 0.08, max(++corr, 5))`~~  → `max(current_hp * 0.04, max(++corr, 3))` **magic** damage at the end of it's turn, ~~damage from the player will heal it by `min(max_hp * 0.01, (damage_taken + corr) * 0.03)`~~ → The enemy takes `min(damage_taken, damage_taken - (++corr))` damage. When damage taken - the corr value reaches <= 0, heal for: `min(corr * 0.75, abs(damage_taken - (++corr) * max_hp * 0.01))`. corruption grows only if the enemy corruption > 0. corr grows after each turn the enemy takes.


## learning spells/abilities:
I will add new consumable loot drops/shop items (like TMs) that teach you spells and abilities, natural level up spell learning (again... pokemon who?), and give some roles starting spells (looking at you mages and necros).

## mana generation:
resting succesfully gives up to 30% of max mana back, natural per turn 2% max mana regeneration, mana potions (consumable to be added to shop) that fill you with 20 mana (or fill to full if max mana <= 20.... somehow).

## items:
Adding the new items also means that I will make it so the healing/spell learning (and probably future consumables) can be used out of combat.
I am also thinking of loot upgrading option (loot stat upgrading which costs gold), and loot selling.

new enemies (sorted):

> I know that more on the easier side enemies need to be added, so I will add some according to the magical patch theme, while also adding other power level enemies too.

|name|corr|hp|attack|def|speed|luck|
|----|----|----|----|----|----|----|
|Banshee|0|13|8|2|0|-12|
|Elf|0|13|8|0|11|7|
|Fairy|0|12|3|11|25|7|
|Living armor|5|200|0|70|0|0|
|Unicorn|0|20|8|2|15|10|
|Vampire|0|9|-15|2|6|0|
|Werewolf|1|23|13|9|20|4|


new roles (sorted):

> Some new roles as well, mostly fitting the theme.
The thought line is to expand the amount of choices, so some may hit similar stat lines or be well tuned.

|Class|Strength|Agility|Intelligence|Defence|Magic|Luck|
|----|----|----|----|----|----|----|
|Dwarf|7|3|5|7|3|0|
|Elf|4|7|6|4|5|2|
|Satyr|2|7|9|3|4|4|
|Tank|0|-5|2|12|1|5|

new items (sorted):

- Health potion: consumable, upon usage, heal for 20 HP, costs 15 gold, always available and doesn't go out of stock.
- Mana potion: consumable, upon usage, gain 20 mana, costs 15 gold, always available and doesn't go out of stock.
- Scroll of doom: consumable, upon usage learn the cursed spell 'DOOM', spell base damage: 10, single target, costs 8 mana, necros start with the consumable in their inventory.
- Beam staff: equipment, 0,0,3,0,3,1, special equipment passive: While equipped; spell "hyper beam" enters your spells tab automatically, spell mana cost: entire mana pool, spell base damage: int(max(5, mana * 0.40)), single target, rarity 12, purchase-able
- Mana rod: equipment, 0,0,15,0,0,0, rarity: 5.
- Thunder apprentice: consumable in combat, once per combat,on usage, call an AOE lightning that deals 6 damage. non droppable, rarity 25 purchase-able. Special consumable quest; use Thunder apprentice 6 times, becomes to Thunder disciple.
- Thunder disciple: consumable in combat, once per combat, on usage, call an AOE thunder that deal 12 damage, non droppable, 0 rarity, not purchase-able. Special consumable quest; use Thunder disciple 6 times, becomes to Thunder master.
- Thunder master: consumable in combat, once per combat, on usage, call an AOE storm that deal 18 damage, non droppable, 0 rarity, not purchase-able.
- Blade rush: consumable, on usage, learn blade rush ability, 22 mana cost, for 4 turns deal max(4, int(str * 0.8 + abs(mag) * 0.4)) physical AOE damage, you cannot make any other action during those 4 turns.
- Mana surge book: consumable, on use learn the spell mana surge, spell mana; 5, +5 each cast in combat, spell damage: 2, +2 each cast in combat. undroppable, not purchase-able, mages start with this consumable in their inventory.





## miscellaneous updates:
- Sort roles alphabetically
- Sort descriptions alphabetically (by roles)
- Add new roles descriptions