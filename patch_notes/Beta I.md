# PYRPG BETA I:

- Big achivements; PYRPG gameplay loop is fully functioning! ALPHA II goals were met and beyond achieved: combat and -x stats fully developed!

### Current features:
- Combat loop and stats fully operating in harmony - but leveling and gold/loot wasn't made yet.
- Combat turns/initiation.
- Project re-arrangment for better readability.

### Next features/ in the making:
- Save deletions (didn't implement last time).
- Adjust auto saves not to trigger in case user asked not to save their progress.
- Actual gold and loot drops.
- EXP gain, and level ups.
- Possibility for stat arranging upon level up (choose which stats to raise).
- Further features beyond combat; resting %healing and only heal when chosing to rest and succeeding, rather than passive between combat full heals.
- Rest success rate; choosing to rest can fail and lead into combat instead.
- Choice to go to town - shopping for loot and gold usage, possibility for town quests implementation
- Enemy groups a chance to tackle 2-3 enemies of the same types/creature.
- More enemies!
- Possible enemy encountering based on player level/stats
- Evasion adjustments

### **Feature implementation info:**
__________________
> Save deletion:
 It is a given users might not enjoy the journey they started and want to start out a new with the same name - that is where deletions come in power. I think on same name given the option to delete should come.

> auto save triggers adjustment: Users who don't want to save at first should not be auto-saved either. Manual saving should be made upon level ups, rests, in town. Users accepting saves will be auto saved on the opportunities. Leaving it to player choices only.

> Gold/loots: An RPG game is expected to have this sort of drops, I will implement a simple loot and gold system and expand upon them after-

> EXP/leveling: Same as loot and gold it is expected to be seen on an RPG game, it is also satisfying to see :p

> Stat raising choice: This one is an interesting concept, yet feels cool. instead of auto raising priority stats per role or stats read. Though I might leave it for later

> Rest & resting success: right now each combat you can heal to full, which is pretty wonky. I think a luck check for both resting chance and heal % (up to 30% of max hp). failing the rest chance will trigger a combat. rest odds are currently `min(60,max(20, luck))% not including -luck stats!`

> Town: complex thinking; choice to go to town, yet I think there can be like a "distance" system - like how far you are from town, and also luck check to return to town without combat on the way... Other than that yes- an actual town to go to, rest, buy gear, and possibly get quests from.

> enemy groups: chance to encounter groups instead of 1, making the player need to handle multiple enemies at once, might give groups random speeds each to have a non fixed initiation.

> More enemies: Enemies don't vary that much, will expand.

> Encounter fairness: currently in combat you can encounter any enemy, which some can kill low stats/level players and feel unfair. while (currently) deaths have no punishments, higher encounter rates for enemies that are better for the player progress can be a good idea.


> Evasion: I will cap evasion to 35% to all things stacking +evasion loot (whenever loot comes) shouldn't peak 35% either

## Systematic updates:

Going forward with the planned updates, player saves have been converted into json system, since working with json and mass data is better.
Do note that each user gets their own json player(s) save file, it will be distributed once user asks the game to save their data.

> **saving and bulk data system:** ~~`players.csv`~~ → `players.json`.




# **Balance Adjustments:**
## -stats


### -strength stats:

On tests, -strength users healing felt too strong for their self damage. Adjusted it so the formula heal < self damage.

> -Strength: Debuff: After attacking you take ~~abs(-str)~~ → `abs(-str) + int(max_hp * 0.01)` damage, Benefit: hitting enemies heals you by  ~~`int(sqrt(missing HP + damage done) + abs(-str * 1.5))`~~  → `min(int(sqrt(missing_hp + damage_done) * 0.5), int(self_damage * 0.75))`


### -Agility stats:

-agi initiation being last on every case felt a little weird, so now if you have -agi and face a lower speed enemy (example, player == -5, enemy == -9), you start before them.
Reworked -agi as a whole adding another debuff:

> -Agility: Debuff: **Act last, `*new:* unless  enemy speed is lower than you` `*new*: max(20, 60 - abs(-agi))% odds to flee battles.` Benefit: your slowness confuses enemies ~~`min(35, (abs(-agi)))%`~~ → `-min(15, max(5, abs(-agi)))%` enemy accuracy** 


### -Intelligence stats:

-int power creep formula looks too strong, edited formula and adjusted to return a whole number.

> -intelligence: Debuff: ~~`min(50, abs(-int) + 5)%`~~ → `min(35, abs(-int) + 5)%` chance to attack a different enemy, Benefit: You find enemies weak points faster dealing  ~~`(2 * (abs(-int)) - ( highest stat / 10))`~~ → `int(0.08 * damage) + int(min(abs(-int) * 0.75, max(highest_stat, 0) // 8))` bonus damage.

### -Defence stats:
-def was unbalanced with it's alpha II state. Following the same pattern, I will adjust them accordingly.

> -Defence: Debuff: Getting hit makes you take ~~`(abs(-def))`~~ → `max(max_hp * 0.05, abs(-def))` bonus damage, Benefit: you reflect ~~int((damage taken * 1.5 + (abs(-def))) / 2.5)~~ → `max(15, min(35, max(damage_taken, abs(-def)) * 0.35))%` flat damage back (flat damage means damage before the bonus)

### -magic stats:

cursed magic users felt like they got the most deadly debuff, remaking debuff and adding a small debuff addition

Also: -magic stat lowering curse now applies to a random enemy stat each successful magical hit, instead of one fixed stat at a time/combat.

> -magic: Debuff: Magic attacks drain **~~(abs(-mag))%~~** → `min(25, abs(-mag))%` from your MAX HP (temporary, restores after combat), `*new*: get 15% less EXP`. Benefit: **Each magic attack has** `min(65, int(sqrt(abs(-mag)) * 10))%` chance to lower a **randomly picked** enemy stat `*new*; by min(7, abs(-mag))`

### -luck stats:

As you might of read -luck players will have a worse time to get rest chances, that will be an added feature added to -luck as well.

> -Luck: Debuff: `-(min(35, abs(-lck)))%` accuracy, lower loot ~~rolls~~  → **odds** and `*new:* resting odds are max(20, 35 - abs(-lck) * 0.48)%` Benefit: Successful attacks are unavoidable

### HP calculation:
Health is a little problematic in its current state, depending only on Def + Str stats. While relying on those two is intended, I'd like roles with fewer points in these stats to also have a fighting chance, and be able to design more roles going forward without worrying about breaking HP balance.

> hp calculation: ~~`abs((strength + defence) / 0.2)`~~ → `max(22, abs((Strength + Defence) * 3.5)))`

## enemy -stats & corruption

### enemy corruption:

enemy hp and corruption split was a smart move, but enemies stacking infinetly with (corr++) after their turn can make it so a player can just wait for very long periods for the battle to just end by itself. Balancing that logic.


> Corruption: The enemy recieves ~~`(++corr)`~~ → `max(current_hp * 0.08, max(++corr, 5))` damage at the end of it's turn, damage from the player will heal it by ~~`min(hp, damage_taken * corr * 1.2) / 100)`~~ → `min(max_hp * 0.01, (damage_taken + corr) * 0.03)`

### enemy -attack:

Interestingly enemy -attack formula had capping, but it didn't look like enough. Also made it so things are read more understandably:

> -Attack: The enemy deals ~~0~~ → `max(0, 15 + (-att))` damage, but will leech player HP and heal itself based on the flat ~~`min(10, abs(-atk) / 100)%`~~ → `min(15, abs(-atk) * 0.46)%` of the attack value


### enemy -defence:
enemies -def was almost there, but needed tweaks as well.

> -Defense: The enemy takes ~~`+min(20, abs(-def))%`~~ →  `+max(3, abs(-def) * 0.75)` **bonus** damage from attacks, but will returns ~~`(damage / 100 + abs(-def))`~~ → `min(5, (damage_taken + abs(-def)) * 0.2)%` of the **flat** damage taken back (flat == before bonus)

### enemy -speed

Following players -agi changes, the rerouting is done here too

> -Speed: ~~The player will always strike -speed enemies first, the enemy's attacks are unavoidable~~ → **Act last, unless the player's agi stat is lower than you.** `*new*: min(15, abs(-spd) * 0.3)% higher chance to succesfully flee from -spd enemies`, -spd enemy attacks cannot be avoided.

### enemy -luck:

Enemies -luck formula on stat lowering made no sense logically and could reach 0 at many cases.

Also: same as -magic, -luck enemies stat lowering curse applies to random player stat each successful hit instead of one stat at a time/combat.

> enemy -luck: The enemy has a `min(45, abs(-lck) * 1.5)%` to hit, **each successful hit curses a randomly sellected player stat** lowering it by **`min(4, abs(-lck))`**

*side note that last patch's curse logic still stands:*
  > - Positive stats (>0): Reduced by curse amount (minimum 0)
 > - Negative stats (<0): Increased by curse amount (maximum 0) 
 > - Zero stats (=0): Remain at 0.


 ## enemies balance:

 Some enemy stats were garbled, so Alpha II adjustment were rewritten over enemies.csv (look at ALPHA II enemy balance changes).

 Moving on, the following enemies stats will change this time in ascending alphabetical order:

| Name | Corruption | HP | Attack | Defense | Speed | Luck |
|-------|----|-----------|--------|---------|-------|------|
|Bear|0|22|~~9~~ → 11|~~6~~ → 9|~~5~~ → 6|~~5~~ → 2|
|Cursed human|15|~~42~~ → 40|~~2~~ → 9|-5|~~3~~ → 10|-5|
| Demon | 0 | 30 | ~~30~~ → 14 | 15 | ~~8~~ → 12 | ~~-40~~ → -25|
|Giant ant| 0 | ~~16~~ → 22| ~~8~~ → 12 | 21 | ~~4~~ → 2 | ~~3~~ → 0 |
|Imp|0|~~3~~ → 14|~~2~~ → 6|0|40|~~16~~ → -7|

 ## new enemies:
|Name|Corruption|HP| Attack | Defense | Speed | Luck |
|-----|----|------|------|------|-------|------|
|Cursed Priest|0|25|10|-8|8|-15|
|Feral Cultist|0|20|-6|10|10|5|
|Harpy|0|14|9|2|25|12|
|Plague Rat Swarm|12|10|5|2|15|-6|
|Rustbound Automaton|0|40|12|-10|5|2|
|Skeleton|0|18|8|14|3|4|
|Troll|0|150|35|40|1|3|
|Wraith|0|16|-4|3|-18|6|