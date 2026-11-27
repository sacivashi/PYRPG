# PYRPG v 1.0.7:
## Unlocks, and a whole lot of flavor!

> Taking off from version 1.0.6, time to give you things to chase, and a game that talks back.

### The road to 1.1:

This one got big. Like, bigger than the magic patch big. So instead of one giant drop, it comes out in stops, each one playable on its own. This is stop 3 of 4.

|Version|What's in it|
|---|---|
|1.0.5|Charisma, the quest board rework, Pirate, new items & enemies, and the other updates|
|1.0.6|Encounters: merchants, chests, mimics, cooks, sculptures (boons & curses), events, and Halt!|
|1.0.7|Unlocks, the Journal, and all the flavor text|
|1.1|Enemies with brains: the main event|

### what changed?

last stop (1.0.6):

- Passive encounters: merchants (and thieves), chests (and mimics), cooks.
- Sculptures: boons & curses, you find out which after praying.
- Random events & adventures, and Halt! in town.


## Unlocks:

- Unlocks: PYRPG has always been an open book, but content you unlock through tasks adds replay-ability, and it's satisfying to earn.

Coming through like a truck, here are current specific un-lockable things;
> classes:
    
    1: As a mage, defeat 15 enemies with -lck stat, or as a mage, find and equip a certain item.
    2: With any class, be defeated 20 times, or as a warrior, lower your magic stat to be <= 0.
    3: With any class, block at least 80 physical damage with defending (cumulative), or with any class, raise your defense stat to be >= 10.
    4: With any class, pray to a sculpture 20 times (cumulative).
    5: With any class, complete 5 quests that gain charisma. (0 charisma or -charisma quests don't count).

> Enemies:

    - 1: Do a certain quest involving priest*. Got to make players feel some regret.
    - 2: Do a certain quest involving townsfolk*. Got to make players feel some regret.
    - 3: In combat, heal a cumulative sum of 45 HP from attacking.
    - 4: Reach a max HP value of 100.

> Items:

    - 1: spend cumulative 55 mana.
    - 2: Beat 6 zombies.
    - 3: Lower/Raise enemy stats to become 0.
    - 4: Encounter the same enemy 11 times.

> How unlocks look in game:

Locked classes show up as ??? at class selection, with their hint and how far you've got:

    Choose a role:
      druid, dwarf, elf, mage, pirate, ranger, rogue, satyr, warrior

    Locked:
      ???  As a mage, defeat 15 enemies with -lck   (4/15)
      ???  Be defeated 20 times                     (7/20)
      ???  Pray to a sculpture 20 times             (12/20)

New town option, the Journal: everything you've unlocked, and everything you haven't (yet):

    === Journal ===
    Classes   0/5   Enemies   1/4   Items   0/4

    [Enemies]
      ???            unlocked
      ???            Do a certain quest involving priest
      ???            In combat, heal 45 HP from attacking   (31/45)

And when you unlock something, you'll know:

    You defeated Zombie!
      ✦ Unlocked: ??? ✦

...well, most of the time. Some unlocks are a bit quieter about it:

    ...something followed you out of town.

>> Unlock progress counts across all your characters, so dying 20 times on one and 0 on another still adds up. Your failures are shared, cherish them.


## new classes:
|Class|Strength|Agility|Intelligence|Charisma|Defense|Magic|Luck|
|---|---|---|---|---|---|---|---|
|???|???|???|???|???|???|???|???|


## Encounters but tastier:

- slaying an enemy with 1 hit now says (40%): "you brutally slayed (enemy) in 1 hit" or "You sure you aren't too strong for this area? Becuase you just took that x in 1 hit". Or "One punch man is you!" Or "Dayum their HP is just gone, poof.".
- Enemy fleeing a battle gives out some flavor (35%): like "x was too afraid to keep facing you, so it fled {on dropping stuff:} and at with that it lost ...". "The cowardous x fled battle {on dropping stuff:} luckily, they dropped ....". "Can't believe x fled this fight, {on drops:} atleast I can find victory on ....". "x fled, {drops:} and dropped ...". "Well didn't anticipate x to just run, {drops:} oh well let's take the .... and leave then.".
    - On -cha: "You were so ugly, x couldn't hold it any longer so it fled. {drops:} just take the .... and don't make me look at you too please.". "No wonder x chose to give up, your face is a puke fest... {drops:} still some .... left though..". "Your vile aura made x run to their momma. {drops:} joy on their ... drops.
    - On high end cha: "Don't blame me I am unsure why would x go away either {drops:} oh hey shiny ....! .". "I guess they were taken breathless by your handsome self that x decided to not fight any longer.. {drops:} oh well, stuff!". "x ran off... so what?! just sway your hair be pretty {drops:} and take the remanence!"
- Resting success (55%): "zZzZ", "snore sounds", "Miserable no more!", "Wish I could rest as much as you right now!", "Had a good nap?", "Wipe that drool off ya, we got adventure to find!", "Keep up, you'll remember to buy potions eventually.", "looking for nuts?", "You sleep very loudly"
- Resting failure (25%): "You light the fire, as you do x appears, out of nowhere.", "You turn on your mattress, and as you turn back x appears, how nice.", "As you lay back, you suddenly notice x lays next to you, in a sexy pose... strange.", "You are about to rest, but your spidey senses sense x", "You may not rest now, there are monsters nearby", "You may not rest now, because I said so", "Miserable as usual huh", "Awh you trying to sleep? But we just reached the best part... x attack!".
- Winning combat with 100% ~ 75% HP (20%): "Guess I will play with you next time!", "Yes!", "Winner winner chicken dinner", "Now eat them!", "A winner is you", "Wow so big and strong", "Too easy", "Easy peasy", "You won that with skill", "You could do that with eyes closed", "woah! bam! pow!", "Remember that you won? yeah it was just now I know!".
- Winning combat with 74% ~ 50% HP (15%): "A few scratches, but it was worth it", "Could always go better", "Oof no worries you'll jog it off", "Hmm not as satisfying", "You won with hard work".
- Winning combat with 49% ~ 1% HP (15%): "That was a real struggle bus", "Do we get a zenkai boost? No? Darn.", "We be struggling", "Maybe it's prime time to return to town.", "Ohh tough one aren't you?", "Next hit could be the last you take, consider your steps!"
- Level ups (75%): "You feel a little taller", "They grow up so fast", "level up!", "Wonder where all that exp goes to...", "Now you can use that anvil... wrong game again.", "A number just went up."
- Learning spell\ability by level (55%): "Wow you are so smart!", "Can you learn how to take breaks too?", "So many calculations!", "Learn it? I barely know it!", "What was it called now?", "Don't forget to scream it's name whenever you use it!"
- Learning spell\ability by item (25%): "That was very long to read", "Too long to read for me!", "How many lines of code was that again?", "You still scrolling through that?", "This x is bigger than I thought!", "So long, so..... boring.", "A bookworm as well aren't we?"
- On being slayed by an enemy (30%): "Guess x was too tough for you", "Couldn't rest, right?", "X had you in the first half...", "You'd get X next time champ", "[player's name], you cannot give up now, get up!", "revive? 3...2...1... oh wait this is not this type of game...", "R.I.P [player's name], they were the hero we needed but not deserved", "Wait, lemme put you back a couple of steps!", "You lost!", "Heh, noob."
- slayed and losing an item (40%): "aaaaaand it's gone! referring to your .... by the way", "You dropped something, it was ....!", "The earth giveth and the earth taketh your ....", "your bag feels lighter, checking out you see you no longer have ....!", "Oops dropped your glasses!... erm I mean your ....."
- slayed town revival (35%): Wait, lemme put you back a couple of steps... oops guess you need to restart", "[player's name] got kicked.... to town", "And stay there!", "I'm gonna take your horse to the old town... and you too", "Well, at least there you are safe.", "And so, it ends, where it began.", "An apple a day, keeps the wild away.".
- Slayed and losing gold and n > 0 (20%): "Congrats you are n coins poorer!", "Glad these coins aren't made of diamonds, because you just lost n of them!", "You shake your pockets and see that you are n gold less... you actually counted all that?", "How sad, those n coins could be converted into something far better", "Need a donation? you lost n gold".
- Slayed losing gold and n <= 0 (40%): "You got slain so many times that now you need donations for real!","Maybe you need to start thinking about your career options...","You have so much gold that you lost none of it!... oh wait opposite, you don't have enough to even lose it!","So now you are poor too, I thought I'd seen everything.","Even a piece of bread needs to spare you at this rate!"
- Evading attacks (15% odds to appear): "You awake your ultra instinct and....", "You become neo, and evade x non existent bullets!", "You are so quick you evade x attack by only moving your head!", "You seen that coming, didn't you?", "You evade the attack. Sweet moves!", "Your evasion tactics are so funky! looks like dancing!", "Evasion ftw".
- Physical Attacking (10% appearance): "Go for the head!", "Hit harder!", "And so you try to hit them and...", "Oh boy, action time!", "Let me rate your hit.... x tier", "Shoryuken!", "How does it feel to spam 1?", "Oh yes I like those numbers!".
- Missing attacks (45%): "Wh- what?!", "Careful, you almost hit yourself there", "The enemy is right there", "Are you serious?!", "Sneaky x!", "x slid pass that one", "No worries you'd get used to the skill shots!", "Could it be? Ultra instinct?!", "Funny one, now land it!", "Unlucky.. probably in a literal sense.", "Is your weapon is shorter than you thought?", "toastie", "Even I could hit x from my own screen!".
- Magical attacking (13%): "Abracadabra!", "Alakazam!", "Wingardium leviosuhhhh", "Fantasma!", "Reaching the arcane depths you use ....", "Some magical hocus pocus!", "Sparkly shiny magic stuff!", "wizard 101 who?", "Look mom, no wands!", "Oh yes I have the brain power", "Gun shot!... but it's magic!", "Magic goes brrrrrrr", "Unlimited powerrrrrr!"
- Cursed spell usage (13%): "Hocus pocus your stats are now irrelavant!", "I smell black magic", "Hexagonal force! wrong hex type?", "Get swallowed by darkness!", "hsssssss", "Bow!", "Weaken.. or strengthen, it depends!", "Now which stat shall it be?", "*evil laugh*".
- Fleeing successfully (35%): "You bravely ran away", "Sir [player's name] ran away", "[player] cowardly fled", "You do know doing that achieves nothing but shame, right?", "{insert cartoony running sounds here}", "Let's run for it scoobs!", "Enemy too scary?", "No doubt here, you left x in the dust.", "Look at em zooming!"
- Fleeing fail (35%): "You ran away... in a circle!", "You tried to run, but your feet won't co-op", "It's seems as though, you are grounded", "You go for a sprint, but x held the tip of your... outfit?", "Guess we cannot run away now Scoobs", "Sir [player] can't bravely run away", "Mysterious powers teleport you back into combat as you distance yourself", "You run, but as you do, you notice only the combat area is loading, you are screwed.", "You trip on a teeny tiny rock, baka. Good thing fall damage doesn't exist."
- Attempting to flee death encounter (85%): "What'd you expect?", "Not this time....", "Death is undeniable...", "You chose this....", "I told you....", "You asked, didn't you?", "You reached so far, let it end.", "No.", "This is basically god, running expands your doom", "Nope.", "Tick, tock", "I AM HERE, JUST FOR YOU.", "You attempted to flee, but its Death", "The fear value is too high to flee". **not landing the flavors says "cannot flee"**
