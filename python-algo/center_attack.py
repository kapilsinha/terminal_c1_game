import copy
import math
import random

import gamelib


"""
Handles the logic to place 'attack' units if we attack through the center.
Attack phase involves placing Pings and/or EMPs and/or scramblers in order to
score points and/or damage the opponent's firewall.
"""
class CenterAttack(object):
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

    def update_passive_defense(self, game_state, passive_defense):
        '''
        1. Adds the top left and right filters ([1, 13], [26, 13]) to the
           priority map with absurdly high priority to make sure they get added
        2. Tries to add a diagonal set of filters to guide our attack units
           away from their natural path (intuition is that the opponent is
           trying to guide us towards their defenses)
        Note that we deliberately do not just create them and instead add them to
        the priority map because we don't want to override more important defenses
        We set its priority to just above the priority of the (6, 11) destructor.
        '''
        # Increase priority of [1, 13], [26, 13] to ENSURE they are added back
        side_filter_priority_overrides = {((1, 13), FILTER, 'spawn'): 1000,
                                          ((26, 13), FILTER, 'spawn'): 1000}
        passive_defense.set_passive_defense_priority_overrides(side_filter_priority_overrides)

        center_attack_start_location_options = [[13, 0], [14, 0]]
        best_location = self._least_damage_spawn_location(game_state, center_attack_start_location_options)
        self.start_side = 'left' if best_location == [13, 0] else 'right'

        # Add diagonal set of 5 filters
        path = game_state.find_path_to_edge(best_location)
        if path is None:
            gamelib.debug_write("[attack.py] Attempted to find path to edge from a blocked position." \
            "[13, 0] and [14, 0] should never contain stationary units")
            return

        path_location_at_row_13 = next((location for location in path if location[1] == 13), None)
        if path_location_at_row_13 is None:
            gamelib.debug_write("[attack.py] Path to edge never hit row 13." \
            "We blockaded ourself in during center attack...should never happen")
            return

        if path_location_at_row_13 < 11:
            destructor_6_11_priority = passive_defense.actual_passive_defense_to_priority[((6, 11), DESTRUCTOR, 'spawn')]
            priority_overrides = {((7, 11), FILTER, 'spawn'): destructor_6_11_priority + .5,
                                  ((8, 11), FILTER, 'spawn'): destructor_6_11_priority + .4,
                                  ((9, 11), FILTER, 'spawn'): destructor_6_11_priority + .3,
                                  ((10, 12), FILTER, 'spawn'): destructor_6_11_priority + .2,
                                  ((11, 13), FILTER, 'spawn'): destructor_6_11_priority + .1}
            passive_defense.set_passive_defense_priority_overrides(priority_overrides)
        elif path_location_at_row_13 > 16:
            priority_overrides = {((20, 11), FILTER, 'spawn'): destructor_6_11_priority + .5,
                                  ((19, 11), FILTER, 'spawn'): destructor_6_11_priority + .4,
                                  ((18, 11), FILTER, 'spawn'): destructor_6_11_priority + .3,
                                  ((17, 12), FILTER, 'spawn'): destructor_6_11_priority + .2,
                                  ((16, 13), FILTER, 'spawn'): destructor_6_11_priority + .1}
            passive_defense.set_passive_defense_priority_overrides(priority_overrides)

    def deploy_units(self, game_state):
        '''
        Deploy attack units through the center.
        '''
        if start_side == 'left':
            start_location = [13, 0]
        else:
            start_location = [14, 0]

        num_bits = int(game_state.get_resource(BITS))

        # We assume it takes 2 hits to take out a ping (which is true iff the ping
        # goes by an encryptor, which is generally the case). This is likely more
        # telling than the damage calculation approach
        estimated_num_hits_by_destructors = self.estimate_num_hits_by_destructors(game_state, start_location)

        # This is a very rough estimate (assuming opponent hasn't deployed anything)
        # but estimated_points_scored = num_pings - (estimated_num_hits_by_destructors // 2)
        estimated_points_scored = num_bits - (estimated_num_hits_by_destructors // 2)

        if estimated_points_scored > 5: # arbitrary threshold
            self.ping_attack(self.start_side, game_state)
        else:
            self.emp_attack(self.start_side, game_state)

    def ping_attack(self, start_side, game_state):
        '''
        Deploys only pings from [13, 0] if start_side = 'left', [14, 0] if start_side = 'right'
        Purpose is a purely quick (albeit weak) attack
        '''
        start_location = [13, 0] if start_side == 'left' else [14, 0]
        game_state.attempt_spawn(PING, start_location, int(game_state.get_resource(BITS)))

    def emp_attack(self, start_side, game_state):
        '''
        Deploys mostly EMPs (and two scramblers for protection).
        If start_side = 'left':
        1. Two scramblers are deployed on [13, 0]
        2. All EMPs are deployed on the first of [1, 12], [2, 11], [3, 10] that
        has no destructors that can attack (e.g. if [1, 12] has a destructor that
        can attack but [2, 11] does not, we deploy on [2, 11]).
        Note that [3, 10] must always be safe from destructors
        If start_side = 'right'
        1. Two scramblers are deployed on [14, 0]
        2. All EMPs are deployed on the first of [26, 12], [25, 11], [14, 10] that
        has no destructors that can attack
        '''
        # Hard-coding the costs of these units (scrambler is 1, EMP is 3)
        num_scramblers_to_deploy = 2
        num_emps_to_deploy = (int(game_state.get_resource(BITS)) - num_scramblers_to_deploy) // 3
        if start_side == 'left':
            game_state.attempt_spawn(SCRAMBLER, [13, 0], num_scramblers_to_deploy)
            if len(game_state.get_attackers([1, 12], 0)) == 0:
                game_state.attempt_spawn(EMP, [1, 12], num_emps_to_deploy)
            elif len(game_state.get_attackers([2, 11], 0)) == 0:
                game_state.attempt_spawn(EMP, [2, 11], num_emps_to_deploy)
            else:
                game_state.attempt_spawn(EMP, [3, 10], num_emps_to_deploy)
        else:
            game_state.attempt_spawn(SCRAMBLER, [14, 0], num_scramblers_to_deploy)
            if len(game_state.get_attackers([26, 12], 0)) == 0:
                game_state.attempt_spawn(EMP, [26, 12], num_emps_to_deploy)
            elif len(game_state.get_attackers([25, 11], 0)) == 0:
                game_state.attempt_spawn(EMP, [25, 11], num_emps_to_deploy)
            else:
                game_state.attempt_spawn(EMP, [24, 10], num_emps_to_deploy)

    def estimate_damage_by_destructors(self, game_state, location):
        path = game_state.find_path_to_edge(location)
        if path is None:
            gamelib.debug_write("[attack.py] Attempted to find path to edge from a blocked position." \
            "[13, 0] and [14, 0] should never contain stationary units")
            return -1 # we will assume this never happens. If so, we accept we're screwed
        damage = 0
        for path_location in path:
            # Get number of enemy destructors that can attack the final location and multiply by destructor damage
            damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(DESTRUCTOR, game_state.config).damage_i
        return damage

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

    def _least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            damage = self.estimate_damage_by_destructors(game_state, location)
            damages.append(damage)

        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]
