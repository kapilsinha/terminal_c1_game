import copy
import math
import random

from center_attack import CenterAttack
from left_attack import LeftAttack
from right_attack import RightAttack
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
        self.left_attack = LeftAttack(config)
        self.right_attack = RightAttack(config)
        # Must be 'left', 'right', or 'center' before calling deploy units
        # i.e. you must compute attack type first
        self.attack_type = None

    def compute_attack_type(self, game_state):
        # TODO: More complex logic involving paths here
        opponent_destructor_locations = game_state.get_opponent_stationary_unit_type_to_locations()[DESTRUCTOR]
        count_left_destructors = len([loc for loc in opponent_destructor_locations if loc[0] <= 4])
        count_right_destructors = len([loc for loc in opponent_destructor_locations if loc[0] >= 23])

        if min(count_left_destructors, count_right_destructors) >= 2:
            self.attack_type = 'center'
        elif count_left_destructors < count_right_destructors:
            self.attack_type = 'left'
        elif count_right_destructors < count_left_destructors:
            self.attack_type = 'right'
        else:
            self.attack_type = random.choice(['left', 'right'])

    def update_passive_defense(self, game_state, passive_defense):
        '''
        Increase priority of encryptors by 13 points.
        Then do attack_type-specific passive defense updates
        '''
        for x, priority in passive_defense.actual_passive_defense_to_priority.items():
            location, firewall_unit_type, action = x
            if firewall_unit_type == ENCRYPTOR:
                passive_defense.actual_passive_defense_to_priority[x] = priority + 13

        self.get_attack().update_passive_defense(game_state, passive_defense)

    def deploy_units(self, game_state):
        '''
        Deploy attack units
        '''
        self.get_attack().deploy_units(game_state)
        # Not necessary, but makes sure compute_attack_type is called next time
        self.attack_type = None

    def get_attack(self):
        if self.attack_type == 'center':
            return self.center_attack
        elif self.attack_type == 'left':
            return self.left_attack
        elif self.attack_type == 'right':
            return self.right_attack
        raise ValueError(f"Attack type must be 'center', 'left', or 'right'.  Found {self.attack_type}")
