import copy
import math
import random

from center_attack import CenterAttack
import gamelib


"""
Handles the logic to place 'attack' units.
Attack phase involves placing Pings and/or EMPs and/or scramblers in order to
score points and/or damage the opponent's firewall.
"""
class Attack(object):
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

        self.center_attack = CenterAttack(config)

    def update_passive_defense(self, game_state, active_move, passive_defense):
        '''
        Increase priority of encryptors by 13 points.
        Then do attack_type-specific passive defense updates
        '''
        for x, priority in passive_defense.actual_passive_defense_to_priority.items():
            location, firewall_unit_type, action = x
            if firewall_unit_type == ENCRYPTOR:
                passive_defense.actual_passive_defense_to_priority[x] = priority + 13

        if active_move == 'attack_center':
            self.center_attack.update_passive_defense(game_state, passive_defense)
        else:
            raise ValueError("Active move must be 'attack_center'")

    def deploy_units(self, game_state, active_move):
        '''
        Deploy attack units
        '''
        # TODO: We need to add attacks on the left and right side
        # (note that this requires deleting a filter on the left or right side
        # and barricading the center).
        if active_move == 'attack_center':
            self.center_attack.deploy_units(game_state)
        else:
            raise ValueError("Active move must be 'attack_center'")
