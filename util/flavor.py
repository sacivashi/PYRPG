"""Flavor text (v1.0.7): the game talking back.

FLAVOR maps a moment to (chance %, lines). say("missed", enemy="Wolf") rolls the chance and, if it
hits, prints one random line with the placeholders filled in: {enemy}, {name} (the player), {item},
{gold}, {tier}. It uses its own random generator, so a line showing up (or not) never shifts the
dice the game itself rolls.

Adding a line is adding a string; adding a moment is one FLAVOR entry plus a say() call where it
happens.
"""
import random

_rng = random.Random()

TIERS = ["S", "A", "B", "C", "D", "F"]

FLAVOR = {
    # --- combat --------------------------------------------------------------------------------
    "one_hit": (40, [
        "You brutally slayed the {enemy} in 1 hit.",
        "You sure you aren't too strong for this area? Because you just took that {enemy} in 1 hit.",
        "One punch man is you!",
        "Dayum, their HP is just gone, poof.",
    ]),
    "evade": (15, [
        "You awake your ultra instinct and....",
        "You become Neo, and evade {enemy}'s non-existent bullets!",
        "You are so quick you evade the {enemy}'s attack by only moving your head!",
        "You saw that coming, didn't you?",
        "You evade the attack. Sweet moves!",
        "Your evasion tactics are so funky! Looks like dancing!",
        "Evasion ftw.",
    ]),
    "attack": (10, [
        "Go for the head!",
        "Hit harder!",
        "And so you try to hit them and...",
        "Oh boy, action time!",
        "Let me rate your hit.... {tier} tier.",
        "Shoryuken!",
        "How does it feel to spam 1?",
        "Oh yes, I like those numbers!",
    ]),
    "missed": (45, [
        "Wh- what?!",
        "Careful, you almost hit yourself there.",
        "The enemy is right there.",
        "Are you serious?!",
        "Sneaky {enemy}!",
        "The {enemy} slid past that one.",
        "No worries, you'd get used to the skill shots!",
        "Could it be? Ultra instinct?!",
        "Funny one, now land it!",
        "Unlucky.. probably in a literal sense.",
        "Is your weapon shorter than you thought?",
        "Toastie.",
        "Even I could hit the {enemy} from my own screen!",
    ]),
    "magic": (13, [
        "Abracadabra!",
        "Alakazam!",
        "Wingardium leviosuhhhh!",
        "Fantasma!",
        "Reaching the arcane depths, you use {item}....",
        "Some magical hocus pocus!",
        "Sparkly shiny magic stuff!",
        "Wizard 101 who?",
        "Look mom, no wands!",
        "Oh yes, I have the brain power.",
        "Gun shot!... but it's magic!",
        "Magic goes brrrrrrr.",
        "Unlimited powerrrrrr!",
    ]),
    "cursed_spell": (13, [
        "Hocus pocus, your stats are now irrelevant!",
        "I smell black magic.",
        "Hexagonal force! ...wrong hex type?",
        "Get swallowed by darkness!",
        "Hsssssss.",
        "Bow!",
        "Weaken.. or strengthen, it depends!",
        "Now which stat shall it be?",
        "*evil laugh*",
    ]),
    "flee": (35, [
        "You bravely ran away.",
        "Sir {name} ran away.",
        "{name} cowardly fled.",
        "You do know doing that achieves nothing but shame, right?",
        "{{insert cartoony running sounds here}}",
        "Let's run for it, Scoobs!",
        "Enemy too scary?",
        "No doubt here, you left the {enemy} in the dust.",
        "Look at 'em zooming!",
    ]),
    "flee_fail": (35, [
        "You ran away... in a circle!",
        "You tried to run, but your feet won't co-op.",
        "It seems as though you are grounded.",
        "You go for a sprint, but the {enemy} held the tip of your... outfit?",
        "Guess we cannot run away now, Scoobs.",
        "Sir {name} can't bravely run away.",
        "Mysterious powers teleport you back into combat as you distance yourself.",
        "You run, but as you do, you notice only the combat area is loading. You are screwed.",
        "You trip on a teeny tiny rock, baka. Good thing fall damage doesn't exist.",
    ]),
    "flee_death": (85, [
        "What'd you expect?",
        "Not this time....",
        "Death is undeniable...",
        "You chose this....",
        "I told you....",
        "You asked, didn't you?",
        "You reached so far, let it end.",
        "No.",
        "This is basically god, running expands your doom.",
        "Nope.",
        "Tick, tock.",
        "I AM HERE, JUST FOR YOU.",
        "You attempted to flee, but it's Death.",
        "The fear value is too high to flee.",
    ]),
    # --- after a fight ---------------------------------------------------------------------------
    "win_high": (20, [  # 75% ~ 100% HP left
        "Guess I will play with you next time!",
        "Yes!",
        "Winner winner chicken dinner.",
        "Now eat them!",
        "A winner is you.",
        "Wow, so big and strong.",
        "Too easy.",
        "Easy peasy.",
        "You won that with skill.",
        "You could do that with eyes closed.",
        "Woah! Bam! Pow!",
        "Remember that you won? Yeah, it was just now, I know!",
    ]),
    "win_mid": (15, [  # 50% ~ 74%
        "A few scratches, but it was worth it.",
        "Could always go better.",
        "Oof, no worries, you'll jog it off.",
        "Hmm, not as satisfying.",
        "You won with hard work.",
    ]),
    "win_low": (15, [  # 1% ~ 49%
        "That was a real struggle bus.",
        "Do we get a zenkai boost? No? Darn.",
        "We be struggling.",
        "Maybe it's prime time to return to town.",
        "Ohh, tough one, aren't you?",
        "Next hit could be the last you take, consider your steps!",
    ]),
    "slain": (30, [
        "Guess the {enemy} was too tough for you.",
        "Couldn't rest, right?",
        "The {enemy} had you in the first half...",
        "You'd get the {enemy} next time, champ.",
        "{name}, you cannot give up now, get up!",
        "Revive? 3...2...1... oh wait, this is not this type of game...",
        "R.I.P. {name}, they were the hero we needed but not deserved.",
        "Wait, lemme put you back a couple of steps!",
        "You lost!",
        "Heh, noob.",
    ]),
    "lost_item": (40, [
        "Aaaaaand it's gone! Referring to your {item}, by the way.",
        "You dropped something, it was your {item}!",
        "The earth giveth and the earth taketh your {item}.",
        "Your bag feels lighter. Checking it out, you see you no longer have your {item}!",
        "Oops, dropped your glasses!... erm, I mean your {item}.",
    ]),
    "town_revival": (35, [
        "Wait, lemme put you back a couple of steps... oops, guess you need to restart.",
        "{name} got kicked.... to town.",
        "And stay there!",
        "I'm gonna take your horse to the old town... and you too.",
        "Well, at least there you are safe.",
        "And so, it ends where it began.",
        "An apple a day keeps the wild away.",
    ]),
    "lost_gold": (20, [
        "Congrats, you are {gold} coins poorer!",
        "Glad these coins aren't made of diamonds, because you just lost {gold} of them!",
        "You shake your pockets and see that you are {gold} gold less... you actually counted all that?",
        "How sad, those {gold} coins could be converted into something far better.",
        "Need a donation? You lost {gold} gold.",
    ]),
    "broke": (40, [  # slain with nothing to lose
        "You got slain so many times that now you need donations for real!",
        "Maybe you need to start thinking about your career options...",
        "You have so much gold that you lost none of it!... oh wait, opposite, you don't have enough to even lose it!",
        "So now you are poor too. I thought I'd seen everything.",
        "Even a piece of bread needs to spare you at this rate!",
    ]),
    # --- resting -----------------------------------------------------------------------------------
    "rested": (55, [
        "zZzZ",
        "*snore sounds*",
        "Miserable no more!",
        "Wish I could rest as much as you right now!",
        "Had a good nap?",
        "Wipe that drool off ya, we got adventure to find!",
        "Keep up, you'll remember to buy potions eventually.",
        "Looking for nuts?",
        "You sleep very loudly.",
    ]),
    "rest_fail": (25, [
        "You light the fire, and as you do, a {enemy} appears out of nowhere.",
        "You turn on your mattress, and as you turn back a {enemy} appears. How nice.",
        "As you lay back, you suddenly notice a {enemy} lying next to you, in a sexy pose... strange.",
        "You are about to rest, but your spidey senses sense a {enemy}.",
        "You may not rest now, there are monsters nearby.",
        "You may not rest now, because I said so.",
        "Miserable as usual, huh.",
        "Awh, you trying to sleep? But we just reached the best part... {enemy} attack!",
    ]),
    # --- growing ---------------------------------------------------------------------------------------
    "level_up": (75, [
        "You feel a little taller.",
        "They grow up so fast.",
        "Level up!",
        "Wonder where all that EXP goes to...",
        "Now you can use that anvil... wrong game again.",
        "A number just went up.",
    ]),
    "learn_level": (55, [
        "Wow, you are so smart!",
        "Can you learn how to take breaks too?",
        "So many calculations!",
        "Learn it? I barely know it!",
        "What was it called now?",
        "Don't forget to scream its name whenever you use it!",
    ]),
    "learn_item": (25, [
        "That was very long to read.",
        "Too long to read for me!",
        "How many lines of code was that again?",
        "You still scrolling through that?",
        "This {item} is bigger than I thought!",
        "So long, so..... boring.",
        "A bookworm as well, aren't we?",
    ]),
}


# v1.1: an enemy fleeing the fight. (without a drop, with one) pairs, by how you look:
# Charisma below 0 is "ugly", FLED_PRETTY_AT or more is "pretty"
FLED_CHANCE = 35
FLED_PRETTY_AT = 8
FLED = {
    "normal": [
        ("The {enemy} was too afraid to keep facing you, so it fled.",
         "The {enemy} was too afraid to keep facing you, so it fled... and with that, it lost {item}."),
        ("The cowardly {enemy} fled the battle.",
         "The cowardly {enemy} fled the battle. Luckily, it dropped {item}."),
        ("Can't believe the {enemy} fled this fight.",
         "Can't believe the {enemy} fled this fight. At least I can find victory in {item}."),
        ("The {enemy} fled.",
         "The {enemy} fled, and dropped {item}."),
        ("Well, didn't anticipate the {enemy} to just run.",
         "Well, didn't anticipate the {enemy} to just run. Oh well, let's take the {item} and leave then."),
    ],
    "ugly": [
        ("You were so ugly, the {enemy} couldn't hold it any longer, so it fled.",
         "You were so ugly, the {enemy} couldn't hold it any longer, so it fled. Just take the {item} and don't make me look at you too, please."),
        ("No wonder the {enemy} chose to give up, your face is a puke fest...",
         "No wonder the {enemy} chose to give up, your face is a puke fest... still, there's {item} left though.."),
        ("Your vile aura made the {enemy} run to its momma.",
         "Your vile aura made the {enemy} run to its momma. Joy, it dropped {item}."),
    ],
    "pretty": [
        ("Don't blame me, I am unsure why the {enemy} would go away either.",
         "Don't blame me, I am unsure why the {enemy} would go away either. Oh hey, shiny {item}!"),
        ("I guess the {enemy} was taken breathless by your handsome self, it decided not to fight any longer..",
         "I guess the {enemy} was taken breathless by your handsome self, it decided not to fight any longer.. oh well, stuff! ({item})"),
        ("The {enemy} ran off... so what?! Just sway your hair and be pretty.",
         "The {enemy} ran off... so what?! Just sway your hair, be pretty, and take the remnants! ({item})"),
    ],
}


def fled_line(enemy, drop=None, charisma=0):
    """An enemy-fled line (35%), picked by your Charisma and whether it dropped something; or None"""
    if _rng.uniform(0, 100) >= FLED_CHANCE:
        return None
    mood = "ugly" if charisma < 0 else "pretty" if charisma >= FLED_PRETTY_AT else "normal"
    plain, dropped = _rng.choice(FLED[mood])
    return (dropped if drop else plain).format(enemy=enemy, item=drop)


def line(moment, **values):
    """Roll the moment's chance: one of its lines with the placeholders filled, or None"""
    chance, lines = FLAVOR[moment]
    if _rng.uniform(0, 100) >= chance:
        return None
    values.setdefault("tier", _rng.choice(TIERS))
    return _rng.choice(lines).format_map(_Blank(values))


def say(moment, **values):
    """Print a flavor line for this moment, if the chance hits. Returns the line (or None)."""
    text = line(moment, **values)
    if text:
        print(f"  » {text}")
    return text


class _Blank(dict):
    """format_map helper: a placeholder nobody filled in reads as "it" instead of crashing"""
    def __missing__(self, key):
        return "it"


def win_moment(hp, max_hp):
    """Which "you won" moment fits how much HP you walked away with"""
    share = hp / max_hp if max_hp else 0
    if share >= 0.75:
        return "win_high"
    return "win_mid" if share >= 0.5 else "win_low"
