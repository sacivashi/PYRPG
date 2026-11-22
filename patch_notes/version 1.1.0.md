# PYRPG v 1.1:
## Enemies but with brains!

> Taking off from version 1.0.7. Remember how enemies only ever attack, and fights are just spamming 1? Not anymore.

### The road to 1.1:

This one got big. Like, bigger than the magic patch big. So instead of one giant drop, it comes out in stops, each one playable on its own. This is stop 4 of 4.

|Version|What's in it|
|---|---|
|1.0.5|Charisma, the quest board rework, Pirate, new items & enemies, and the other updates|
|1.0.6|Encounters: merchants, chests, mimics, cooks, sculptures (boons & curses), events, and Halt!|
|1.0.7|Unlocks, the Journal, and all the flavor text|
|1.1|Enemies with brains: the main event|

### what changed?

last stop (1.0.7):

- Unlocks: classes, enemies and items to earn, tracked in the new Journal.
- Flavor text, everywhere. So much of it.

And now for the main event:


## enemies move logic:

Following the solutions enemies encountered now have their nuggings installed to them:

> enemy thought process:
>> - on 100% ~ 80% of HP, priorities dishing out attacks
>>> New attack types:
>>> - Charge attack: the enemy prepares a large scale attack, takes the enemy a turn to charge up, but damages player for (enemy attack * 1.5) damage
>>> - Charge attack but you are a healer (-attack):  takes the enemy a turn to charge up, sears * 1.3 of siphon value (siphon value stays the same). charge attacks have a chance to happen, and will prompt with "(enemy name) bides..." or "Enemy name is smiling wickedly"
>>>> odds: 60 normal, 20 charged, 20 defend
>> - 80% ~ 45% of HP, choose between attempting to defend and attacking:
>>> 50/10/40 odds of attacking charging defending; if defending and player physically attacks, enemy has a 15% chance to counter attack
>>> - counter attack: The enemy strikes the player for attack value + a portion of defense value int(max(0,def * 0.45))
>> - 45% and less:
>>> Enemy will start thinking about fleeing, fleeing odds depend on it's speed + luck int(max(0,min(15,spd * 0.44 + lck * 0.44)))%, 30/10/60 attack/charge/defend if failing. Enemy fleeing has 30% to drop some gold (3 ~ 8) or a loot, but won't give exp. nor count towards a defeat x number quest

> enemy thought process, but it's groups:
>> - all members at 100% ~ 80% of HP, the one member uses the solo phase 1 odds (60/20/20)
>>> other member or 2 members may support attack, or defend themselves (60 norm/30 charge/10 def)
>> - any single member at 80% ~ 45% of HP, choose between attempting to defend and attacking
>>> other member or 2 members might attack, defend, or attempt to heal the most injured, non -attack member (45 atk/15 chrg/20 def/20 heal), can't heal selves.
>>>> successful heal attempts heal the injured enemy for 12% missing HP.
>> - single member at 45% and less:
>>> Same as singular, just if that one flees, the rest stay. The others use the phase 2 support odds, so they may still heal it.

**those nuggings don't affect any special encounters (eg; mimics, death)** 

> With that, adding some more to enemy def:
>> Enemies choosing to defend, will block; `def% + min(10, max(0,def * 0.65))` physical damage
