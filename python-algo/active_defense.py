import copy
import math
import random

import gamelib


"""
Handles the logic to place 'active defense'.
Active defense involves the placement of scramblers to defend against the
opponent's likely attack. We deploy active defense in the turns where we
are not attacking.
"""
class ActiveDefense(object):
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

    def deploy_units(self, game_state, num_scramblers=None):
        '''
        Deploys scramblers in specific locations
        '''
        if num_scramblers is None:
            num_scramblers = self.num_scramblers_to_deploy(game_state)
        self.basic_scrambler_deploy_strategy(game_state, num_scramblers)

    def basic_scrambler_deploy_strategy(self, game_state, num_scramblers):
        '''
        Basic strategy: Just deploy all the scramblers alternating at (8, 5) and (19, 5)
        Locations are somewhat arbitrary but based on playing the game, seem good
        '''
        left_deploy_location = [11, 2]
        right_deploy_location = [16, 2]
        num_deployed_on_left_side = num_scramblers // 2
        num_deployed_on_right_side = num_scramblers - num_deployed_on_left_side
        if random.random() < .5:
            # Swap em randomly to keep things interestings
            num_deployed_on_left_side, num_deployed_on_right_side = num_deployed_on_right_side, num_deployed_on_left_side
        game_state.attempt_spawn(SCRAMBLER, left_deploy_location, num=num_deployed_on_left_side)
        game_state.attempt_spawn(SCRAMBLER, right_deploy_location, num=num_deployed_on_right_side)

    def num_scramblers_to_deploy(self, game_state):
        '''
        num_scramblers_to_deploy = ceil[(opponent_bits // 3) / 2]
        = ((opponent_bits // 3) + 1) // 2
        '''
        enemy_num_bits = int(game_state.get_resource(BITS, 1))
        return ((enemy_num_bits // 3) + 1) // 2
