import copy
import math
import random

import gamelib
from blockade import Blockade

"""
Handles the logic to place 'attack' units if we attack through the right side.
Attack phase involves placing Pings and/or EMPs and/or scramblers in order to
score points and/or damage the opponent's firewall.
"""
class RightAttack(object):
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
        Adds the top left filter [1, 13] to the priority map with absurdly
        high priority to make sure it gets added
        '''
        # Increase priority of [1, 13] to ENSURE it is added back
        side_filter_priority_overrides = {((1, 13), FILTER, 'spawn'): 1000}
        passive_defense.set_passive_defense_priority_overrides(side_filter_priority_overrides)

    def deploy_units(self, game_state):
        '''
        Deploy attack units through the right.
        '''
        opponent_destructor_locations = game_state.get_opponent_stationary_unit_type_to_locations()[DESTRUCTOR]
        # Number of destructors on column 23 or right and row 15 and below
        count_nearby_destructors = len([loc for loc in opponent_destructor_locations if loc[0] >= 23 and loc[1] <= 15])
        if count_nearby_destructors <= 1:
            self.ping_attack(game_state)
        else:
            # Do EMP attack
            if random.random() < .85:
                self.emp_attack_for_damage(game_state)
            else:
                self.emp_attack_for_points(game_state)

    def ping_attack(self, game_state):
        '''
        Ping attack is always trying to score points quickly.
        Deploy 6 pings on [9, 4] (to self destruct if need be) and the rest on [8, 5]
        We make sure to blockade center to guide the pings right
        '''
        self.blockade.blockade_center(game_state)
        first_wave_size = 6
        second_wave_size = int(game_state.get_resource(BITS)) - first_wave_size
        game_state.attempt_spawn(PING, [10, 3], first_wave_size)
        game_state.attempt_spawn(PING, [9, 4], second_wave_size)

    def emp_attack_for_damage(self, game_state):
        '''
        Deploys EMPs on the left side but force them to go left purely to do
        damage. Also send a few scramblers
        '''
        self.blockade.blockade_center(game_state)
        num_scramblers_to_deploy = 1
        num_emps_to_deploy = (int(game_state.get_resource(BITS)) - num_scramblers_to_deploy) // 3
        game_state.attempt_spawn(EMP, [14, 0], num_emps_to_deploy)
        game_state.attempt_spawn(SCRAMBLER, [25, 13], num_scramblers_to_deploy)

    def emp_attack_for_points(self, game_state):
        '''
        Deploys EMPs on the right side to score points (and also do damage).
        Can theoretically deploy at any point on the right side but we always choose [14, 0]
        Also send a few scramblers
        '''
        self.blockade.blockade_center(game_state)
        num_scramblers_to_deploy = 1
        num_emps_to_deploy = (int(game_state.get_resource(BITS)) - num_scramblers_to_deploy) // 3
        game_state.attempt_spawn(EMP, [13, 0], num_emps_to_deploy)
        game_state.attempt_spawn(SCRAMBLER, [25, 13], num_scramblers_to_deploy)
