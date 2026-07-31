# PYRPG-BETA I:

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

### **Feature implementation info:**
__________________
> Save deletion:
 It is a given users might not enjoy the journey they started and want to start out a new with the same name - that is where deletions come in power. I think on same name given the option to delete should come.

> auto save triggers adjustment: Users who don't want to save at first should not be auto-saved either. Manual saving should be made upon level ups, rests, in town. Users accepting saves will be auto saved on the opportunities. Leaving it to player choices only.

> Gold/loots: An RPG game is expected to have this sort of drops, I will implement a simple loot and gold system and expand upon them after-

> EXP/leveling: Same as loot and gold it is expected to be seen on an RPG game, it is also satisfying to see :p

> Stat raising choice: This one is an interesting concept, yet feels cool. instead of auto raising priority stats per role or stats read. Though I might leave it for later

> Rest & resting success: right now each combat you can heal to full, which is pretty wonky. I think a luck check for both resting chance and heal % (up to 30% of max hp). failing the rest chance will trigger a combat. rest odds are currently `min(55,max(20, luck)% not including -luck stats!`

> Town: complex thinking; choice to go to town, yet I think there can be like a "distance" system - like how far you are from town, and also luck check to return to town without combat on the way... Other than that yes- an actual town to go to, rest, buy gear, and possibly get quests from.

> enemy groups: chance to encounter groups instead of 1, making the player need to handle multiple enemies at once, might give groups random speeds each to have a non fixed initiation.

> More enemies: Enemies don't varry that much, will expand.

> Encounter fairness: currently in combat you can encounter any enemy, which some can kill low stats/level players and feel unfair. while currently deaths have no punishments, higher encounter rate for enemies that are better for the player progress can be a good idea.


### **Adjustments:**
## -luck stats:

As you might of read -luck players will have a worse time to get rest chances, that will be an added feature added to -luck as well....

> -Luck: Debuff: `-(min(35, abs(-lck)))%` accuracy, lower loot ~~rolls~~  --> **odds**, **resting odds fixed to 20%** Benefit: Successful attacks are unavoidable

## -magic stats:

cursed magic users felt like they got the most deadly debuff so I am adding more and adjusting it a little! c:

> -magic: Debuff: Magic attacks drain ~~(abs(-mag))%~~ --> ***`min(25, abs(-mag))%`*** from your MAX HP (temporary, restores after combat), **get 30% less EXP**. Benefit: Your spells have ***`min(65, int(sqrt(abs(-mag)) * 10))%`*** chance to debuff enemy stats

## -strength:

While testing -strength users healing felt too strong for their self hurting. Adjusting it so heal < self damage

> -Strength: Debuff: After attacking you take ~~abs(-str)~~ --> ***`(abs(-str) + 1% max HP)`*** damage, Benefit: hitting enemies heals you by  ~~`int(sqrt(missing HP + damage done) + abs(-str * 1.5))`~~ --> ***`min(int(sqrt(missing_hp + damage_done) * 0.5), self_damage - 1)`***