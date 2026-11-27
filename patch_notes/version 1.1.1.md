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
[1] New Player; [2] Load/Delete;
```

> "New game"
- I want this part to change this part to prompt you to input a name the player will use along all their saved adventures, like example:
```
You chose to start a new game.
To start you off, please input a name to save your adventures behind
name:
```
- After so prompts the usual choose a name and role, only that choosing an existing name will just say "This character exists, please use a different name"

- That matters because I want that different player name may be able to use a similar adventurer name that is separate from the one who started it.

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

> "Load"