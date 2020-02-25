import copy
import math
import random

import gamelib
from blockade import Blockade

"""
Handles the logic to place 'attack' units if we attack through the left side.
Attack phase involves placing Pings and/or EMPs and/or scramblers in order to
score points and/or damage the opponent's firewall.
"""
class LeftAttack(object):
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

        self.blockade = Blockade(config)

    def update_passive_defense(self, game_state, passive_defense):
        '''
        Adds the top right filter [26, 13] to the priority map with absurdly
        high priority to make sure it gets added
        '''
        # Increase priority of [26, 13] to ENSURE it is added back
        side_filter_priority_overrides = {((26, 13), FILTER, 'spawn'): 1000}
        passive_defense.set_passive_defense_priority_overrides(side_filter_priority_overrides)

    def deploy_units(self, game_state):
        '''
        Deploy attack units through the left.
        '''
        opponent_destructor_locations = game_state.get_opponent_stationary_unit_type_to_locations()[DESTRUCTOR]
        # Number of destructors on column 4 or left and row 15 and below
        count_nearby_destructors = len([loc for loc in opponent_destructor_locations if loc[0] <= 4 and loc[1] <= 15])
        if count_nearby_destructors <= 1:
            self.ping_attack(game_state)
        else:
            # Do EMP attack
            if random.random() < .5:
                self.emp_attack_for_damage(game_state)
            else:
                self.emp_attack_for_points(game_state)

    def ping_attack(self, game_state):
        '''
        Ping attack is always trying to score points quickly so it always
        starts at [14, 0]
        We make sure to blockade center to guide the pings left
        '''
        self.blockade.blockade_center(game_state)
        game_state.attempt_spawn(PING, [14, 0], int(game_state.get_resource(BITS)))

    def emp_attack_for_damage(self, game_state):
        '''
        Deploys EMPs on the left side but force them to go left purely to do
        damage. Deploy at [10, 3] since [11, 3], [12, 4] are blockaded off
        '''
        self.blockade.blockade_left(game_state)
        num_emps_to_deploy = int(game_state.get_resource(BITS)) // 3
        game_state.attempt_spawn(EMP, [10, 3], num_emps_to_deploy)

    def emp_attack_for_points(self, game_state):
        '''
        Deploys EMPs on the right side to score points (and also do damage).
        Can theoretically deploy at any point on the right side but we always choose [14, 0]
        Also send a few scramblers on [7, 6] (so they reach [1, 13] at the same time)
        '''
        self.blockade.blockade_center(game_state)
        num_emps_to_deploy = int(game_state.get_resource(BITS)) // 3
        num_scramblers_to_deploy = int(game_state.get_resource(BITS)) % 3
        game_state.attempt_spawn(EMP, [14, 0], num_emps_to_deploy)
        game_state.attempt_spawn(SCRAMBLER, [7, 6], num_scramblers_to_deploy)
