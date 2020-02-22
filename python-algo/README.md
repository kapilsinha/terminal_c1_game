# Our Algo

## File Overview

```
starter-algo
 │
 ├──gamelib
 │   ├──__init__.py
 │   ├──algocore.py
 │   ├──game_map.py
 │   ├──game_state.py
 │   ├──navigation.py
 │   ├──tests.py
 │   ├──unit.py
 │   └──util.py
 │
 ├──algo_strategy.py
 ├──documentation
 ├──README.md
 ├──run.ps1
 └──run.sh
```

### Creating an Algo

To create an algo, simply modify the `algo_strategy.py` file.

### `algo_strategy.py`

This file contains the `AlgoStrategy` class which you should modify to implement
your strategy.

At a minimum you must implement the `on_turn` method which handles responding to
the game state for each turn. Refer to the `starter_strategy` method for inspiration.

If your algo requires initialization then you should also implement the
`on_game_start` method and do any inital setup there.

### `documentation`

A directory containing the sphinx generated documentation, as well as the files required
to build it. You can view the docs at https://docs.c1games.com, or by opening index.html
in documents/_build. You can remake the documentation by running 'make html' in the documentation folder.

### `run.sh`

A script that contains logic to invoke your code. You do not need to run this directly.
See the 'scripts' folder in the Starterkit for information about testing locally. 

### `run.ps1`

A script that contains logic to invoke your code. You shouldn't need to change
this unless you change file structure or require a more customized process
startup. 

### `gamelib/__init__.py`

This file tells python to treat `gamelib` as a bundled python module. This
library of functions and classes is intended to simplify development by
handling tedious tasks such as communication with the game engine, summarizing
the latest turn, and estimating paths based on the latest board state.

### `gamelib/algocore.py`

This file contains code that handles the communication between your algo and the
core game logic module. You shouldn't need to change this directly. Feel free to 
just overwrite the core methods that you would like to behave differently. 

### `gamelib/game_map.py`

This module contains the `GameMap` class which is used to parse the game state
and provide functions for querying it. 

### `gamelib/navigation.py`

Functions and classes used to implement pathfinding.

### `gamelib/tests.py`

Unit tests. You can write your own if you would like, and can run them using
the following command:

    python3 -m unittest discover

### `gamelib/unit.py`

This module contains the `GameUnit` class which holds information about a Unit.

### `gamelib/util.py`

Helper functions and values that do not yet have a better place to live.

## Strategy Overview
1. Update PASSIVE DEFENSE ('firewall' location, action) -> priority map (factor in what `activeMove` is & health of existing defenses). 'action' is either placing a new unit or upgrading an existing unit (note that the priority of upgrading an extra unit must be strictly lower than the priority of creating that unit).
2. (PASSIVE DEFENSE) Iterate down the priority list (nothing priority 0 should be done) and add the corresponding defenses (add filters or encryptor or destructor or upgrade stuff) if it hasn’t been done already until we have MIN_CORES (3-4?) left.
3. Execute `activeMove` (ATTACK or ACTIVE DEFENSE)
4. Decide whether we will ATTACK (if so, where?) or ACTIVE_DEFENSE in next turn —> set activeMove
 - Maybe if num_bits_next_round - num_bits_this_round < THRESHOLD, attack. Otherwise, defend.
 - If attacking, attack on the side with the fewest destructors
 5. Delete the appropriate filters etc. based on value of activeMove (whether you will attack next move and if so, how) and based on health of existing filters and based on number of cores.

### ACTIVE DEFENSE
Commonality:
 - Deploy scramblers (only) but where?
 - Number of scramblers is some function of opponent’s number of bits in the next round
 - Maybe # scramblers = ceil[(opponent_bits // 3) / 2]

#### A) Basic Defense
Deploy scramblers constantly in the same location (or do some dumb alternating thing)

#### B) More Advanced Defense
Somehow predict what the opponent will do for their attack (esp if they do the same thing in every round or if they have only a couple points where they can enter our side - iterate over all their start positions and see at what points they can enter our side) and calculate where to place all the scramblers to minimize (1) points lost and then (2) damage taken

## ATTACK (enum based on type of attack?) - Need several strategies here
 - Where to attack?
 - How to attack? Combine attacking units along with “firewall" units (especially filters to guide our attackers and destructors to destroy opponents’ scramblers)
 - Maybe group into where we are going to attack and then calculate how?

#### A) Attack through middle -> classic attack

#### B) Attack through left -> barricade the middle and delete the filters on left

#### C) Attack through right -> symmetrical to attack through left

#### D) Unique strategy
 - Example: Setting up a line of filters so that EMPs can move along it and attack safely
 - Similar to what happens in the MadroxFactor AI vs Raptor AI
