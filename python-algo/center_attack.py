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
        1. Increases priority of encryptors by 10
        2. Tries to add a destructor on row 11 (the goal is to kill off some attackers
        esp. scramblers) and filters to protect it.
        Note that we deliberately do not just create them and instead add them to
        the priority map because we don't want to override more important defenses
        We set its priority to just below the priority of the (6, 11) destructor.
        Further note that in theory since we could be blockading ourselves
        since we don't track these extra added defenses but this is extremely
        unlikely so we ignore this.
        '''
        # Increase priority of encryptors by 10 points
        for x, priority in passive_defense.actual_passive_defense_to_priority.items():
            location, firewall_unit_type, action = x
            if firewall_unit_type == ENCRYPTOR:
                passive_defense.actual_passive_defense_to_priority[x] = priority + 10

        # Increase priority of destructor + supporting filters
        center_attack_start_location_options = [[13, 0], [14, 0]]
        best_location = self._least_damage_spawn_location(game_state, center_attack_start_location_options)
        self.start_side = 'left' if best_location == [13, 0] else 'right'

        # Spawn destructor on row 11 with protective filters (total cost is 9)
        path = game_state.find_path_to_edge(best_location)
        if path is None:
            gamelib.debug_write("[attack.py] Attempted to find path to edge from a blocked position." \
            "[13, 0] and [14, 0] should never contain stationary units")
        else:
            destructor_location = next((location for location in path if location[1] == 11), None)
            if destructor_location is None:
                gamelib.debug_write("[attack.py] Path to edge did not hit row 11." \
                "We should never block a path from hitting row 11")
            else:
                x, y = destructor_location
                destructor_6_11_priority = passive_defense.actual_passive_defense_to_priority[((6, 11), DESTRUCTOR, 'spawn')]
                priority_overrides = {((x, y + 1), FILTER, 'spawn'): destructor_6_11_priority - .1,
                                      ((x, y), DESTRUCTOR, 'spawn'): destructor_6_11_priority - .2,
                                      ((x - 1, y), FILTER, 'spawn'): destructor_6_11_priority - .3,
                                      ((x + 1, y), FILTER, 'spawn'): destructor_6_11_priority - .3}
                passive_defense.set_passive_defense_priority_overrides(priority_overrides)

    def deploy_units(self, game_state):
        '''
        Deploy attack units through the center.
        '''
        if random.random() < .5:
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

    def _least_damage_spawn_location(self, game_state, location_options):
        """
        This function will help us guess which location is the safest to spawn moving units from.
        It gets the path the unit will take then checks locations on that path to
        estimate the path's damage risk.
        """
        damages = []
        # Get the damage estimate each path will take
        for location in location_options:
            path = game_state.find_path_to_edge(location)
            if path is None:
                gamelib.debug_write("[attack.py] Attempted to find path to edge from a blocked position." \
                "[13, 0] and [14, 0] should never contain stationary units")
                damages.append(1000000) # ghetto way to keep going
                continue
            damage = 0
            for path_location in path:
                # Get number of enemy destructors that can attack the final location and multiply by destructor damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(DESTRUCTOR, game_state.config).damage_i
            damages.append(damage)

        # Now just return the location that takes the least damage
        return location_options[damages.index(min(damages))]
