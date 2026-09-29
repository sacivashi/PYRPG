# PYRPG v 1.0:
## The age of magic:

Welcome to PYRPG! or should I write welcome back?

Regarding Beta I, things are fully written, flows work overall, some edge parts are left for later.

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
#

### **upcoming:**

Imagine this, you boot PYRPG, choose a magical class, you use "magic attack" in combat, and.... it's like you hit the enemy with a physical attack decorated as "magic". Plain as the day you were born.

### **NO MORE**
I am introducing, the age of magic, splitting magic & physical damage. Pokemon gen 3 who?

anyhow, yeah:

- Add mana
- Add spells
- AOE logic (for not only magic users)
- More consumable items and ways to heal out of town and combat rather than being misrable in trying to rest
- Obviously add more quests
- No spells = no magic attacks, cry about it.
- DOT spells/attacks?
- Magical creatures (enemies & roles)

## stats and logic:

*magic reworked:*

> **Spell damage:** `Spell Base Damage × max(0.1, 1 + Magic × 0.1)`. A dedicated caster (high Magic) roughly doubles a spell's base damage. The multiplier is floored at 0.1 (10% of base) so damage can never hit 0 or go negative, no matter how far Magic gets pushed down via leveling.

> **Two spell pools:** `+Magic` learns from the normal spell list. `-Magic` gets their own exclusive **cursed spells** (full power, part of their kit) *and* can also learn from the normal list — just weaker there, since the floor formula above works against a negative Magic stat. Cursed spells stay exclusive to `-Magic`; normal-Magic characters never get access to them.

> **No spell learned?** Selecting Magic Attack with nothing learned shows "you have no spells" and kicks you back to choose a different action (Physical Attack, etc.) instead — doesn't waste the turn on an empty action.

> **-intelligence?:**
>> *adding AOE and hitting a different enemy doesn't make the debuff logical... reworking it!*
>> - going forward mana pool is buffed by abs(int). `mana = max(20, abs(int) * 1.1)`. Also adjusting -int to be more powerful for heavier magic users:
>> - -intelligence: Debuff: `min(35, abs(-int) + 5)%` ~~chance to attack a different enemy~~ → **chance to waste `(spell mana cost * 1.5)`** Benefit: ~~You find enemies weak points faster dealing~~ → **your spells deal** `int(0.08 * damage) + int(min(abs(-int) * 0.75, max(abs(magic), 0) // 8))` bonus **magic** damage **regardless if the debuff applied or not**.

> **-magic?:** 
>> for my next magic (heh get it, magic?) trick what if I told you it was thought of ahead of time... somewhat?
>> - -magic: Debuff: ~~Magic attacks~~ → **cursed spells** ~~drain `min(25, abs(-mag))%` from your MAX HP~~ → cost min(abs(mag), mana_cost * 0.88) HP **instead of mana**, `*new*: get 15% less EXP`. Benefit: **Each ~~magic attack~~ → cursed spell has** `min(65, int(sqrt(abs(-mag)) * 10))%` chance to lower a **randomly picked** enemy stat `*new*; by min(7, abs(-mag))` 
>> - **additionally (and obviously) -mag only can access cursed spells, and deal less damage with normal spells (read line 50). cursed spells deal `Spell Base Damage × max(0.1, 1 + abs(Magic) × 0.1)`**

> -strength:
>> strength curse shouldn't benefit or be damaged by magic
>> Debuff: ~~After attacking~~ → using physical attacks damages you for `abs(-str) + int(**min**(max_hp * ~~0.01~~ → 0.08, **abs(str) * 0.7**)` damage, **whether  you hit or miss the attack** Benefit: ~~hitting~~ → landing physical attacks on enemies heals you for  `min(int(sqrt(missing_hp + damage_done) * 0.5), int(self_damage * 0.75))`

## learning spells:
I will add new consumable loot drops/shop items (like TMs) that teach you spells, natural level up spell learning (again... pokemon who?), and give some roles starting spells (looking at you mages and necros).

## mana generation:
resting succesfully maximum 30% of max mana back, natural per turn 2% max mana regeneration, mana potions (consumable to be added to shop) that fill you with 20 mana (or fill to full if max mana < 20.... somehow).

new enemies (sorted):

|name|corr|hp|attack|def|speed|luck|
|----|----|----|----|----|----|----|
|Elf|0|13|8|0|11|7|
|Fairy|0|12|3|11|25|7|
|Unicorn|0|20|8|2|15|10|
|Vampire|0|9|-15|2|6|0|

new roles (sorted):
|Class|Strength|Agility|Intelligence|Defence|Magic|Luck|
|----|----|----|----|----|----|----|
|dwarf|7|3|5|7|3|0|
|Satyr|2|7|9|3|5|3|

## miscellaneous updates:
- Sort roles alphabetically
- Sort descriptions alphabetically (by roles)
- Add new roles descriptions