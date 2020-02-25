import copy
import math
import random

import gamelib


"""
Handles the logic to blockade our paths.
Blockading involves placing temporary Filters in our defense line to force
our information/attacker units to navigate in a specific way.

Assumes you have 4 cores to deploy filters. Note that it directly builds the
filters as opposed to adding it to the priority map
"""
class Blockade(object):
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

        self.center_locations = [[13, 6], [14, 6]]
        self.left_locations = [[11, 3], [12, 4]]
        self.right_locations = [[15, 4], [16, 3]]

    def blockade_center(self, game_state):
        blockade_locations = self.center_locations
        game_state.attempt_spawn(FILTER, blockade_locations)
        game_state.attempt_remove(blockade_locations)

    def blockade_left(self, game_state):
        blockade_locations = self.left_locations
        game_state.attempt_spawn(FILTER, blockade_locations)
        game_state.attempt_remove(blockade_locations)

    def blockade_right(self, game_state):
        blockade_locations = self.right_locations
        game_state.attempt_spawn(FILTER, blockade_locations)
        game_state.attempt_remove(blockade_locations)

    def blockade_center_and_left(self, game_state):
        blockade_locations = self.center_locations + self.left_locations
        game_state.attempt_spawn(FILTER, blockade_locations)
        game_state.attempt_remove(blockade_locations)

    def blockade_center_and_right(self, game_state):
        blockade_locations = self.center_locations + self.right_locations
        game_state.attempt_spawn(FILTER, blockade_locations)
        game_state.attempt_remove(blockade_locations)
