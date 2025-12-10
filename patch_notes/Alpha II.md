# PYRPG-Alpha II:

`Everything is remade! stuff didn't flow with one another so I scratched allot from everything.`

### New features:
- Saving data should work appropriately now, hopefully.

### next features:
- combat
- initialisation of stats, attack turns 
- save deletions(?)

# future features info:
_____________________________
## enemy stats info:

### Introducing -stats:
**`Enemies with -stat(s) get unique effects:`**

- `-HP: The enemy takes (abs(-hp)++) damage at the end on it's turn, receiving damage from the player will heal it`
- `-Attack: The enemy deals 0 damage, but will heal itself based on the ```min(1%, abs(-atk) / 100)%``` amount when hitting an attack`
- `-Defense: The enemy takes ```+min(20, abs(-def))%``` damage from attacks, but will return ```(damage / 100 + abs(-def))``` of the damage taken back`
- `-Speed: The player will *always* strike -speed enemies first, the enemy's attacks are unavoidable`
- `-Luck: The enemy has a ```min(45, abs(-lck) * 1.5)``` on attacks, the enemy's successful hits *curse* a player's stat lowering them by (abs(-X))`

```*Curse mechanics: Enemies with -Luck curse player stats on hit.
  Example: Enemy with -2 Luck reduces/increases player Strength by 2.
 - Positive stats (>0): Reduced by curse amount (minimum 0)
 - Negative stats (<0): Increased by curse amount (maximum 0) 
 - Zero stats (=0): Remain at 0
```

#### Enemy adjustments:
- ```Jester: 20,6,15,17,20 > -20,4,10,15,22```
- ```Orc: 55,25,8,1,0 > 52,20,10,-5,0```
- ```Spider: 25,5,2,10,6 > 15,3,0,6,8```
- ```Witch: 6,14,3,4,8 > 5,15,1,2,-8```
- ```Giant: 100,22,45,4,8 > 120,20,45,-20,8```
- ```Bat: 5,5,2,15,5 > 10,-5,3,15,5```
- ```Zombie: 11,3,-8,-5,0 > -8,3,-10,-2,-2```


#### New enemy:
- ```Cursed Human: -15,2,-5,3,-5```

### role stats info:
I have decided the player roles can have -x stats:
roles with -x stat(s) get unique effects:

- `-Strength: Debuff: After attacking you take ```(abs(-str))``` damage, Benefit: hitting enemies heals you by ```int(sqrt(missing HP + damage done) + abs(-str * 1.5))``` `
- `-Agility: Debuff: Always act last (-speed enemies not included). Benefit: Incoming attacks are easier to read ```+min(35, (abs(-agi)))%``` dodge rate.`
- `-Intelligence: Debuff: ```min(50, abs(-int) + 5)%``` chance to attack a different enemy, Benefit: you hit harder ```(2 * (abs(-int)) - ( highest stat / 10))``` `
- `-Defence: Debuff: Getting hit makes you take ```(abs(-def))``` damage bonus, Benefit: you deflect damage by ```int((damage taken * 1.5 + (abs(-def))) / 2.5)``` `
- `-Magic: Debuff: Using cursed magic drains ```(abs(-mag))%``` from your MAX HP (temporary, restores after combat) Benefit: Your spells have ```min(65, int(sqrt(abs(-mag)) * 10))%``` chance to debuff enemy stats ``*enemies with 0 stat can't get lower, enemies that get -stat debuffed will be trated as + stat*`` `
- `-Luck: Debuff: ```-(min(35, abs(-lck)))%``` accuracy, lower loot rolls, Benefit: Successful attacks are unavoidable`


role adjustments:

#### ranger base stats felt way too strong for a role that focuses on their agility, I chose to nerf ranger's strength to add up to their agility.
with the new stats in line, ranger role is now the fastest initiative yet.
- ```Ranger: 6,8,5,5,3,7 > 3,11,6,2,2,9```

#### Necromancers just felt like mages, considering how their base stats were very comparable to one another.
Although they should feel different play wise, I felt like they should have unique stats, so now necromancer magic can debuff enemies.
- ```Necromancer: 3,4,9,4,10,5 > 1,2,6,4,-8,5```

### New roles:
Since -x stats introduce new variety, I added 2 more roles to choose from:
- ```forsaken: -2,3,2,10,-2,2```
- ```monk: 5,5,8,-9,3,1```
