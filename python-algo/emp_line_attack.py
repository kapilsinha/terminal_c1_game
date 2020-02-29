import copy
import math
import random

import gamelib


"""
Handles the logic to place 'attack' units if we attack through the center.
Attack phase involves placing Pings and/or EMPs and/or scramblers in order to
score points and/or damage the opponent's firewall.
"""
class EMPLineAttack(object):
    def __init__(self, config):
        # Screw it this is nasty but we gonna copy paste this everywhere to get
        # access to the global variables
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, BITS, CORES
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]
        BITS = 1
        CORES = 0

    def num_bits_required(self, game_state):
        stationary_units = [FILTER, DESTRUCTOR, ENCRYPTOR]
        cheapest_unit = FILTER
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.CORES] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.CORES]:
                cheapest_unit = unit
        cheapest_unit_cost = gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.BITS]
        emp_class = gamelib.GameUnit(EMP, game_state.config)

        return cheapest_unit_cost * 7 


    def deploy_units(self, game_state):
        """
        Build a line of the cheapest stationary unit so our EMP's can attack from long range.
        Unused (this was part of the starter code)
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [FILTER, DESTRUCTOR, ENCRYPTOR]
        cheapest_unit = FILTER
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.CORES] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.CORES]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our EMPs from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn EMPs next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(EMP, [24, 10], 1000)

    def update_passive_defense(self, game_state, passive_defense):
        '''
        Increase priority of encryptors by 13 points.
        Then do attack_type-specific passive defense updates
        '''
        return passive_defense
