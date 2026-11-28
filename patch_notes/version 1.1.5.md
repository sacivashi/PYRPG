```
 ____   __   __  ____    ____     ____ 
|  _ \  \ \ / / |  _ \  |  _ \   / ___|
| |_) |  \ V /  | |_) | | |_) | | |  _ 
|  __/    | |   |  _ <  |  __/  | |_| |
|_|       |_|   |_| \_\ |_|      \____|
                           patch v1.1.5
```

# version 1.1.5, where things settle.

Let's make a hasty start and mess things up a little.

## Last changes:
- Game shell/terminal more colorful and game-like.
- One more role has been added as an unlock next to an item.
- Saves, loads, deletions, unlocks are now personal per player rather than just character. Which also brought better json levels.
- Introduced new game mechanic passive "create" where the character creates a useable item in combat if it doesn't have that item.
- Made some flavors replace the normal text (the ones who fit that).

## Incoming:

Let's have a real chat, allot of mechanics in the game still don't like to make sense.
### Examples: 

- Choosing to return to town and failing keeps you at the same depth you ar at. While the game literally says you have lost the way... And get attacked.
- Cooks give no benefits when you are full HP while it was a little intended it's quite a waste of output lines, I think them selling healing food(s) can make sense too since being able to get outside healing except from town shop and at times wandering merchants will be nice.
- Fast travel, that is quite a big one, first off, you might come to fast travel's....steed? With lacking amount of gold from the maximum depth you reached (let's say you reached 20~ and it costs 40, you have 25 gold, it only tells you depth 1 costs 2, 20 costs 40). the problem is... Okay with my gold which depth can I go to? I am no mathematician!
- More fast travel shenanigans, Okay let's say you travel the depth you reached, you can instantly go deeper... Feels like a cheat really, and in the first place how does the steed even know what depth you reached??? Lol. Might bump down to max(1,depth_reached - 5), or make it go to a jump of depth fives (5,10,15,....) and your dungeon scouting gives them knowledge(?) :D
