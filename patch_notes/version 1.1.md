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
- Thief merchant(s): Same as merchant but buying or selling from/to them makes them suprise attack you (which means, the intiation will be theirs regardless). selling an item + winning combat returns you the item. Buying and winning returns you the gold you wasted, but no item (unless a loot dropped magically). thief merchants aren't called thief merchants, are called merchants. same stats as normal enemy thief.
- Treasure chest(s): Can be "encountered", at any depth, contain some gold (5 ~ 13) and may contain a random loot. Has a chance to be a mimic
- Mimic chest(s): Same as treasure, but choosing to open these makes them surprise attack you, defeating one gives you bonus gold (3 ~ 11). mimics aren't called mimics, just treasure chest.
- Healer(s): (debating to call those cooks) Can be "encountered" at depth 5+, pay int(choosen_hp value * 2.3) and heal that value.
> Sculptures (or boons): Can be "encountered", at depth 5+, prayer sculptures which can be one of the following (will tell you by text):
>
    Of resting: better rest odd for three time (+15%)
    Of survival: higher rest heal for three time (only on success) (+15% missing HP).
    Of Prosperity: Some more gold income (+12% on next win)
    Of Intellect: A boost of exp (+30% on next win)
    Of Growth: Set your max_HP to +15 and then full heal, that max hp stays on till you win combat.
    Of fear: Entering combat, your **charisma** (coming up) stat is multiplied by -1, clears at combat's end.


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

> enemy thought process, but it's groups:
>> -any 100% ~ 80% of HP, one of the group will priorities attacking
>>> 2nd and 3d may support attack, or brace themselves (70 fight/30 brace/defend)
>> - any 80% ~ 45% of HP, choose between attempting to defend and attacking,
>>> 2nd and third might attack, defend, or attemt to heal the most injured, non -attack memeber (45/35/30), can't heal selves.
>>>> succesful heal attempts heal the injured enemy for 12% missing HP.
>> - any 45% and less:
>>> Same as above, just if one flees, the rest that didn't do so stay.

## introducing a new player stat:

I think it is prime time for charisma to be added. Well hello there handsomes.

> - Charisma: shop costs are int(max(0,min(15,cha * 0.48)))% cheaper. You sway other people easier, giving you bonus odds, to not fail with sculptures, not encountring bad encounter types. +int(max(0,min(20, cha * 0.25)))%
> - -Charisma: 
> - Benefeit..?: You are so darn ugly, enemies intend to flee from you all the time (100 to 0% HP... lmao) but have more odds to drop stuff by min(45,abs(cha) * 1.5). 
> - Debuff: You are so darn ugly..(I am sorry lol) that you sway others to make you fail (opposite odds and shop costs from +cha (up to +15% shop costs and up to +20% fail and bad encounters.))
>> charisma stat doesn't benefit combat damage, or encounter calculations

## here are some numbers! (charisma to roles):
|Class|Strength|Agility|Intelligence|**Charisma**|Defence|Magic|Luck|
|---|---|---|---|---|---|---|---|
|druid|4|4|6|**3**|4|6|4|
|dwarf|7|3|5|**1**|7|3|0|
|elf|4|7|6|**7**|4|5|2|
|forsaken|-1|5|3|**-7**|9|-4|4|
|mage|3|4|10|**2**|3|9|5|
|monk|5|5|8|**4**|-9|3|1|
|necromancer|1|4|6|**-5**|5|-8|5|
|ranger|3|11|6|**5**|2|2|9|
|rogue|5|9|5|**7**|4|2|9|
|satyr|2|7|9|**6**|3|4|4|
|tank|0|-5|2|**0**|12|1|5
|warrior|6|4|4|**4**|6|3|1|

aren't the pretty? c:

## More flavorful fighting:

- slaying an enemy with 1 hit now says: "you brutally slayed (enemy) in 1 hit" or "You sure you aren't too strong for this area? Becuase you just took that x in 1 hit". Or "One punch man is you!" Or "Dayum their HP is just gone, poof.".
- Enemy fleeing a battle gives out some flavor: like "x was too afraid to keep facing you, so it fled {on dropping stuff:} and at with that it lost ...". "The cowardous x fled battle {on dropping stuff:} luckily, they dropped ....". "Can't believe x fled this fight, {on drops:} atleast I can find victory on ....". "x fled, {drops:} and dropped ...". "Well didn't anticipate x to just run, {drops:} oh well let's take the .... and leave then.".
    - On -cha: "You were so ugly, x couldn't hold it any longer so it fled. {drops:} just take the .... and don't make me look at you too please.". "No wonder x chose to give up, your face is a puke fest... {drops:} still some .... left though..". "Your vile aura made x run to their momma. {drops:} joy on their ... drops.
    - On high end cha: "Don't blame me I am unsure why would x go away either {drops:} oh hey shiny ....! .". "I guess they were taken breathless by your handsome self that x decided to not fight any longer.. {drops:} oh well, stuff!". "x ran off... so what?! just sway your hair be pretty {drops:} and take the remnance!"
- Resting success (55%): "zZzZ", "snore sounds", "Miserable no more!", "Wish I could rest as much as you right now!", "Had a good nap?", "Wipe that drool off ya, we got adventure to find!", "Keep up, you'll remember to buy potions eventually.", "looking for nuts?", "You sleep very loudly"
- Resting failure (25%): "You light the fire, as you do x appears, oughta nowhere.", "You turn on your matress, and as you turn back x appears, how nice.", "As you lay back, you suddenly notice x lays next to you, in a sexy pose... strange.", "You are bouta rest, but your spidey senses sense x", "You may not rest now, there are monsters nearby", "You may not rest now, cus I said so", "Miserable as usual huh", "Awh you tryna sleep? But we just reached the best part... x attack!".
- Winning combat with 100% ~ 75% HP (20%): "Guess I will play with you next time!", "Yes!", "Winner winner chicken dinner", "Now eat them!", "A winner is you", "Wow so big and strong", "Too easy", "Easy peasy", "You won that with skill", "You could do that with eyes closed", "woah! bam! pow!", "Remember that you won? yeah it was just now I know!".
- Winning combat with 74% ~ 50% HP (15%): "A few scratches, but it was worth it", "Could always go better", "Oof no worries you'll jog it off", "Hmm not as satisfying", "You won with hard work".
- Winning combat with 49% ~ 1% HP (15%): "That was a real struggle bus", "Do we get a zenkai boost? No? Darn.", "We be struggling", "Maybe it's prime time to return to town.", "Ohh tough one aren't you?", "Next hit could be the last you take, consider your steps!"
- Level ups (75%): "You feel a little taller", "They grow up so fast", "level up!", "Wonder where all that exp goes to...", "Now you can use that anvil... wrong game again.", "A number just went up."
- Learning spell\ability by level (55%): "Wow you are so smart!", , "Can you learn how to take breaks too?", "So many calculations!", "Learn it? I barely know it!", "What was it called now?", "Don't forget to scream it's name whenever you use it!"
- Learning spell\ability by item (25%): "That was very long to read", "Too long to read for me!", "How many lines of code was that again?", "You still scrolling through that?", "This x is bigger than I thought!", "So long, so..... boring.", "A bookworm as well aren't we?"
- On being slayed by an enemy: "Guess x was too tough for you", "Couldn't rest, right?", "X had you in the first half...", "You'd get X next time champ", "[player's name], you cannot give up now, get up!", "revive? 3...2...1... oh wait this is not this type of game...", "R.I.P [player's name], they were the hero we needed but not deserved", "Wait, lemme put you back a couple of steps!", "You lost!", "Heh, noob."
- slayed and losing an item: "aaaaaand it's gone! referring to your .... by the way", "You dropped something, it was ....!", "The earth giveth and the earth taketh your ....", "your bag feels lighter, checking out you see you no longer have ....!", "Oops dropped your glasses!... erm I mean your ....."
- slayed town revival: Wait, lemme put you back a couple of steps... oops guess you need to restart", "[player's name] got kicked.... to town", "And stay there!", "I'm gonna take your horse to the old town... and you too", "Well, at least there you are safe.", "And so, it ends, where it begun.", "An apple a day, keeps the wild away.".
- Slayed and losing gold and n > 0: "Congrats you are n coins poorer!", "Glad these coins aren't made of diamonds, because you just lost n of them!", "You shake your pockets and see that you are n gold less... you actually counted all that?", "How sad, those n coins could be converted into something far better", "Need a donation? you lost n gold".
- Slayed losing gold and n <= 0: "You got slain so many times that now you need donations for real!","Maybe you need to start thinking about your career options...","You have so much gold that you lost none of it!... oh wait opposite, you don't have enough to even lose it!","So now you are poor too, I thought I'd seen everything.","Even a piece of bread needs to spare you at this rate!"
- Evading attacks (15% odds to appear): "You awake your ultra instinct and....", "You become neo, and evade x non existent bullets!", "You are so quick you evade x attack by only moving your head!", "You seen that coming, didn't you?", "You evade the attack. Sweet moves!", "Your evasion tactics are so funky! looks like dancing!", "Evasion ftw".
- Physical Attacking (10% appearance): "Go for the head!", "Hit harder!", "And so you try to hit them and...", "Oh boy, action time!", "Let me rate your hit.... x tier", "Shoryuken!", "How does it feel to spam 1?", "Oh yes I like those numbers!".
- Missing attacks: "Wh- what?!", "Careful, you almost hit youself there", "The enemy is right there", "Are you serious?!", "Sneaky x!", "x slid pass that one", "No worries you'd get used to the skillshots!", "Could it be? Ultra instinct?!", "Funny one, now land it!", "Unlucky.. probably in a literal sense.", "Is your weapon is shorter than you thought?", "toastie", "Even I could hit x from my own screen!".
- Magical attacking (13%): "Abracadabra!", "Alakazam!", "Wingardium leviosuhhhh", "Fantasma!", "Reaching the arcane depths you use ....", "Some magical hocus pocus!", "Sparkly shiny magic stuff!", "wizard 101 who?", "Look mom, no wands!", "Oh yes I have the brain power", "Gun shot!... but it's magic!", "Magic goes brrrrrrr", "Unlimited powerrrrrr!"
- Cursed spell usage (13%): "Hocus pocus your stats are now irrelavant!", "I smell black magic", "Hexagonal force! wrong hex type?", "Get swallowed by darkness!", "hsssssss", "Bow!", "Weaken.. or strengthen, it depends!", "Now which stat shall it be?", "*evil laugh*".
- Fleeing successfully (35%): "You bravely ran away", "Sir [player's name] ran away", "[player] cowardly fled", "You do know doing that achieves nothing but shame, right?", "{insert cartoony running sounds here}", "Let's run for it scoobs!", "Enemy too scary?", "No doubt here, you left x in the dust.", "Look at em zooming!"
- Fleeing fail (35%): "You ran away... in a circle!", "You tried to run, but your feet won't co-op", "It's seems as though, you are grounded", "You go for a sprint, but x held the tip of your... outfit?", "Guess we cannot run away now Scoobs", "Sir [player] can't bravely run away", "Mysterious powers teleport you back into combat as you distance yourself", "You run, but as you do, you notice only the combat area is loading, you are screwed.", "You trip on a teeny tiny rock, baka. Good thing fall damage doesn't exist."
- Attempting to flee death encounter (100%): "What'd you expect?", "Not this time....", "Death is undeniable...", "You chose this....", "I told you....", "You asked, didn't you?", "You reached so far, let it end.", "No.", "This is basically god, running expands your doom", "Nope.", "Tick, tock", "I AM HERE, JUST FOR YOU.
".

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

## Mimic added:

|Name|Corruption|HP|Attack|Defense|Speed|Luck|
|---|---|---|---|---|---|---|
|Mimic|0|20|5|8|12|0|
> Mimic > 0 stats get stronger the deeper you are by `(base stats + depth - 1)`, past depth 50 buff are also included. Enemy encounter calculations do not affect Mimics.
>> Same goes for thief merchant, only if it is a thief merchant