import copy
import math

import gamelib


"""
Handles the logic to place 'passive defense'.
Passive defense is the (largely dumb i.e. not based on opponent's moves)
placement of firewall units in order to maintain some defensive configuration.
"""
class PassiveDefense(object):
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

        # Maps (location, firewall_unit_type, place/upgrade)
        left_side_base_passive_defense_to_priority = {
            ((0, 13), FILTER, 'spawn'): 48,
            ((1, 13), FILTER, 'spawn'): 47,
            ((2, 13), FILTER, 'spawn'): 46,
            ((3, 13), FILTER, 'spawn'): 45,
            ((4, 12), FILTER, 'spawn'): 44,
            ((5, 11), FILTER, 'spawn'): 43,
            ((6, 10), FILTER, 'spawn'): 42,
            ((6, 9), FILTER, 'spawn'): 41,
            ((7, 8), FILTER, 'spawn'): 40,
            ((8, 7), FILTER, 'spawn'): 39,
            ((9, 7), FILTER, 'spawn'): 38,
            ((10, 6), FILTER, 'spawn'): 37,
            ((12, 5), DESTRUCTOR, 'spawn'): 36, # absolutely need to deploy this and above in round 1!
            ((11, 5), FILTER, 'spawn'): 35,
            ((12, 6), FILTER, 'spawn'): 34,
            ((6, 12), FILTER, 'spawn'): 33,
            ((7, 11), FILTER, 'spawn'): 32,
            ((6, 11), DESTRUCTOR, 'spawn'): 31,
            ((11, 6), DESTRUCTOR, 'spawn'): 30,
            ((11, 7), FILTER, 'spawn'): 29,
            ((3, 12), DESTRUCTOR, 'spawn'): 28,
            ((3, 12), DESTRUCTOR, 'upgrade'): 27,
            ((8, 10), FILTER, 'spawn'): 26,
            ((7, 10), DESTRUCTOR, 'spawn'): 25,
            ((0, 13), FILTER, 'upgrade'): 24,
            ((1, 13), FILTER, 'upgrade'): 23,
            ((2, 13), FILTER, 'upgrade'): 22,
            ((3, 13), FILTER, 'upgrade'): 21,
            ((4, 12), FILTER, 'upgrade'): 20,
            ((12, 4), ENCRYPTOR, 'spawn'): 19,
            ((12, 3), ENCRYPTOR, 'spawn'): 18,
            ((11, 4), ENCRYPTOR, 'spawn'): 17,
            ((5, 13), FILTER, 'spawn'): 16,
            ((5, 12), DESTRUCTOR, 'spawn'): 15,
            ((5, 13), FILTER, 'upgrade'): 14,
            # upgrades are low priority (because they double damage but not health)
            # Note that it is important to put it in this list in case their priority
            # gets increased
            ((12, 5), DESTRUCTOR, 'upgrade'): 13,
            ((6, 11), DESTRUCTOR, 'upgrade'): 12,
            ((7, 10), DESTRUCTOR, 'upgrade'): 11,
            ((5, 12), DESTRUCTOR, 'upgrade'): 10,
        }
        right_side_base_passive_defense_to_priority = {
            ((27 - x, y), firewall_type, action): priority \
            for (((x, y), firewall_type, action), priority) \
            in left_side_base_passive_defense_to_priority.items()
        }

        # This is the constant, base priority map. NEVER CHANGE IT!
        # It will be slightly modified when placing firewall units
        # The modified verseion is self.actual_passive_defense_to_priority
        self.base_passive_defense_to_priority = {
            **left_side_base_passive_defense_to_priority,
            **right_side_base_passive_defense_to_priority
        }

        self.actual_passive_defense_to_priority = copy.copy(self.base_passive_defense_to_priority)

    def set_passive_defense_priority_overrides(self, override_priority_map):
        '''
        override_priority_map overrides corresponding entries in
        base_passive_defense_to_priority and adds extra entries
        e.g. if override_priority_map = {(0, 13), ENCRYPTOR, 'spawn': 100, (0, 0), FILTER, 'spawn': 99}
        then these dict entries would be placed in self.actual_passive_defense_to_priority
        '''
        self.actual_passive_defense_to_priority.update(override_priority_map)

    def reset_passive_defense_priority(self, game_state):
        '''
        Reset our priority map to our original base priority map
        and delete other defeneses we have put up
        '''
        self.actual_passive_defense_to_priority = copy.copy(self.base_passive_defense_to_priority)
        locations_to_keep = set([x[0] for x in self.base_passive_defense_to_priority.keys()])
        for location in game_state.get_locations_for_our_side():
            if tuple(location) not in locations_to_keep:
                game_state.attempt_remove(location)

    def increase_priority_near_location(self, game_map, location, radius, increase_amount):
        locations_in_circle = game_map.get_locations_in_range(location, radius)
        tuple_locations_in_circle = set([tuple(location) for location in locations_in_circle])
        for key, priority in self.actual_passive_defense_to_priority.items():
            location, firewall_unit_type, action = key
            if location in tuple_locations_in_circle:
                self.actual_passive_defense_to_priority[key] = priority + increase_amount

    def deploy_units(self, game_state, num_cores_to_leave = 4):
        '''
        Places units one by one on the board from high to low priority.
        Does not place any unit with a priority of 0 or lower
        Stops when we have num_cores_to_leave CORES remaining.
        '''
        priority_sorted_passive_defense = [defense for defense, priority \
            in sorted(self.actual_passive_defense_to_priority.items(), \
            key=lambda item: item[1], reverse=True) if priority > 0]
        for location, firewall_unit_type, action in priority_sorted_passive_defense:
            if game_state.get_resource(CORES) - game_state.type_cost(firewall_unit_type)[CORES] < num_cores_to_leave:
                break
            if action == 'spawn':
                num_units = game_state.attempt_spawn(firewall_unit_type, list(location))
            elif action == 'upgrade':
                num_units = game_state.attempt_upgrade(list(location))
            else:
                raise ValueError("Action must be 'spawn' or 'upgrade'")
            # Could use num_units, which shows whether the spawn or upgrade happened but nah