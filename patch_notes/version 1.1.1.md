```
 ____   __   __  ____    ____     ____ 
|  _ \  \ \ / / |  _ \  |  _ \   / ___|
| |_) |  \ V /  | |_) | | |_) | | |  _ 
|  __/    | |   |  _ <  |  __/  | |_| |
|_|       |_|   |_| \_\ |_|      \____|
                           patch v1.1.1
```

# version 1.1.1
Hello Hello. The new era of PYRPG is only starting c:

Overall patches 1.0.0 ~ 1.1.0 were big updates, from this patch and so on, I'll dish out smaller, scaling updates for QOL, UI, and of course adjustments needed. 

## What changed?:

- actions in pyrpg may now return you small usually funky comments, next time the game calls your character ugly, blame me!
- Enemies have actual AI, and always attacking them makes less sense than before (it is intended)
- Players now encounter things that are not only enemies, rejoice!
- As for preparations for this patch, current game terminal (which is still a little dull :C) was updated to look less debug console like.
- Unlocks are boarded in with nails, you can now unlock in game things. There might be more incoming later c: I will write how many of what type without spoiling too much if so


# What is coming up:
## UI revolution:

- As mentioned before, the game terminal is pretty dull the way it is. Yes even after editing it to show HP bars and make non saving players save before combat prompt silent. It is still lacking. 
So I am upgrading the terminal to use built in rich terminal

## The meaning:
- Colorful bars
- Colorful texts
- Better tables
- More sorted out option picking
- Players might need to install it... :p

## What else?

Honestly the game's start is strange, you are recognized to load your adventurer, wherever it is. It isn't the most sense maker.

> new game start screen:
```
 ____   __   __  ____    ____     ____ 
|  _ \  \ \ / / |  _ \  |  _ \   / ___|
| |_) |  \ V /  | |_) | | |_) | | |  _ 
|  __/    | |   |  _ <  |  __/  | |_| |
|_|       |_|   |_| \_\ |_|      \____|
                                vx.x.x

Please choose an option:

[1] New Player; [2] My Adventurers; [3] Exit;
```

> "New Player"
- I want this part to change this part to prompt you to input a name the player will use along all their saved adventures, like example:
```
You chose to create a new user.
To start you off, please input a name to save your adventures behind
your name?:

abc

Welcome abc, let's create your first adventurer.
A new adventure rises in the dawn for player's name, what shall the adventurer name be?
```

- That matters because I want that different player name may be able to use a similar adventurer name that is separate from the one who started it.

> Has another player name?:
```
You chose to create a new user.
To start you off, please input a name to save your adventures behind
your name?:

flood

Apparently, this user name is in existence, would you like to load your data instead? (y/n/leave empty to go back to main) 

y

go to load flow with player's name

n

then we continue....

To start you off, please input a name to save your adventures behind
your name?:

```

> json levels

```
{
"Players" : {
    "Player's name" : {
        "Adventurers" : [{
        
            "name": "",
            "role": "",
            "level": 0,
            "hp": 0,
            "max_hp": 0,
            "stats": {
                "Strength": 0,
                "Agility": 0,
                "Intelligence": 0,
                "Defence": 0,
                "Magic": 0,
                "Luck": 0
            },
            "gold": 0,
            "loot": [
                ""
            ],
            "equipped": null
        }]
        "Unlocks":
        {
            1
            2
            3
        }
    }
}
}
```

> "Load/Delete"
Choosing Load will ask you to type your own player name, and show a list of adventurers you own:

```
Welcome back [player name].
Which character shall we touch?
[1]; char name, char role, level, HP/MP, currently at depth x/in town.
[2]; {Create new adventurer}

1

Load or delete (L\D)?

L: throws you in where you left, other data like stats and etc can be checked in game
D: Delete: prompts the character name as confirmation, then deletes it

2

A new adventure rises in the dawn for player's name, what shall the adventurer name be? (the rest is the same as the usual "Type your name to load your save. Name:" as before.)


and same as before, let's say player has a character named bee:

What shall the adventurer name be?

bee (or Bee since names aren't case sensitive)

This character exists, please use a different name or load it
What shall the adventurer name be?
```

> No load name? [insert mega mind no redacted? meme here]:
```
Input your name to load data from (leave empty to go back):

unaffiliated

No player data for "unaffiliated" found, would you like to make a New plyer with that name? (y/n)

y

Much obliged.
Welcome unaffiliated, let's create your first adventurer.
A new adventure rises in the dawn for player's name, what shall the adventurer name be?

n

Then we continue...
Input your name to load data from (leave empty to go back to main):

after creation and saving;

Input your name to load data from (leave empty to go back):

unaffiliated (or Unaffiliated)

Welcome back unaffiliated.
Which character shall we touch?
```

## into the void:
honestly, the only save data in here is my own play testing saves, as much as I will miss what I did so far, I will void it all, and start a new journey c:. If somehow you got old saves for yourselves I recommend erasing them too, but rejoice in the fact that this save data will now be "players_old.json", added in with "unlocks_old.json" since unlocks are now individual to a player.

## Unlocks:
- Added one more unique role and item to unlock, very explosive!

## Misc:
- Changed "Cut" item learner name to "HM01".
- Some flavor lines now replace the normal lines (if hit).
- HP/MP bars are separated by thin gray frame.
- HP/MP bars show after successful rests.
- Menus are numbered down by columns, rather than parallels.
- Items with rarity set to -1 cannot be sold.
- -1 rarity items can never be found in shops or drop.
- Roles can now have a "create" passive: an item they get at the start of a fight if they don't have one.