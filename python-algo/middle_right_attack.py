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
class MiddleRightAttack(object):
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

    def delete_filters(self, game_state, passive_defense):
        loc = [20, 9]
        game_state.attempt_remove(loc)
        priority_override = {(tuple(loc), FILTER, 'spawn'): 0}
        passive_defense.set_passive_defense_priority_overrides(priority_override)

    def deploy_units(self, game_state):
        '''
        Deploy attack units through the middle right.
        '''
        #opponent_destructor_locations = game_state.get_opponent_stationary_unit_type_to_locations()[DESTRUCTOR]
        #count_nearby_destructors = len([loc for loc in opponent_destructor_locations if loc[0] >= 23 and loc[1] <= 15])
        estimated_num_hits_by_destructors = self.estimate_num_hits_by_destructors(game_state, [20, 6])
        our_num_bits = int(game_state.get_resource(BITS, 0))
        # pretend it takes 2 hits to kill a ping or an EMP (since our encryptors add 15 health)
        if our_num_bits > estimated_num_hits_by_destructors // 2 + 4:
            self.ping_attack(game_state)
        else:
            self.emp_attack(game_state)

    def ping_attack(self, game_state):
        '''
        Ping attack is always trying to score points quickly.
        '''
        num_scramblers = 2
        num_pings = int(game_state.get_resource(BITS)) - num_scramblers
        game_state.attempt_spawn(PING, [20, 6], num_pings)
        game_state.attempt_spawn(SCRAMBLER, [20, 6], num_scramblers)

    def emp_attack(self, game_state):
        '''
        Deploys EMPs on the left side but force them to go left purely to do
        damage. Also send a few scramblers
        '''
        num_scramblers = 2
        num_emps_to_deploy = (int(game_state.get_resource(BITS)) - num_scramblers) // 3
        game_state.attempt_spawn(EMP, [20, 6], num_emps_to_deploy)
        game_state.attempt_spawn(SCRAMBLER, [20, 6], num_scramblers)

    def estimate_num_hits_by_destructors(self, game_state, location):
        path = game_state.find_path_to_edge(location)
        if path is None:
            gamelib.debug_write("[attack.py] Attempted to find path to edge from a blocked position." \
            "[13, 0] and [14, 0] should never contain stationary units")
            return -1 # we will assume this never happens. If so, we accept we're screwed
        num_hits = 0
        for path_location in path:
            # Get number of enemy destructors that can attack the final location
            num_hits += len(game_state.get_attackers(path_location, 0))
        return num_hits
