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

            ((0, 13), FILTER, 'upgrade'): 43,
            ((1, 13), FILTER, 'upgrade'): 42,
            ((2, 13), FILTER, 'upgrade'): 41,
            ((3, 13), FILTER, 'upgrade'): 40,
            ((4, 12), FILTER, 'upgrade'): 39,



            ((5, 11), FILTER, 'spawn'): 38,
            ((6, 10), FILTER, 'spawn'): 37,
            ((7, 9), FILTER, 'spawn'): 36,
            ((8, 8), FILTER, 'spawn'): 35,
            ((9, 7), FILTER, 'spawn'): 34,
            ((10, 6), FILTER, 'spawn'): 33,
            ((11, 5), FILTER, 'spawn'): 32,


            ((3, 12), DESTRUCTOR, 'spawn'): 31,
            ((12, 4), DESTRUCTOR, 'spawn'): 30,
            ((12, 5), FILTER, 'spawn'): 29,


            # makes up an inner wall with the destructors
            ((2, 11), FILTER, 'spawn'): 28,

            # the closer inner wall
            ((11, 4), FILTER, 'spawn'): 27,
            ((10, 3), FILTER, 'spawn'): 26,

            ((2, 12), DESTRUCTOR, 'upgrade'): 25,
            ((4, 12), DESTRUCTOR, 'upgrade'): 24
        }


        right_side_base_passive_defense_to_priority = {
            ((27, 13), FILTER, 'spawn'): 48,
            ((26, 13), FILTER, 'spawn'): 47,
            ((25, 13), FILTER, 'spawn'): 46,
            ((24, 13), FILTER, 'spawn'): 45,
            ((23, 12), FILTER, 'spawn'): 44,

            ((27, 13), FILTER, 'upgrade'): 43,
            ((26, 13), FILTER, 'upgrade'): 42,
            ((25, 13), FILTER, 'upgrade'): 41,
            ((24, 13), FILTER, 'upgrade'): 40,
            ((23, 12), FILTER, 'upgrade'): 39,



            ((22, 11), FILTER, 'spawn'): 38,
            ((21, 10), FILTER, 'spawn'): 37,
            ((20, 9), FILTER, 'spawn'): 36,
            ((19, 8), FILTER, 'spawn'): 35,
            ((18, 7), FILTER, 'spawn'): 34,
            ((17, 6), FILTER, 'spawn'): 33,
            ((16, 5), FILTER, 'spawn'): 32,


            ((24, 12), DESTRUCTOR, 'spawn'): 31,
            ((26, 12), DESTRUCTOR, 'spawn'): 30.5
            ((15, 4), DESTRUCTOR, 'spawn'): 30,
            ((15, 5), FILTER, 'spawn'): 29,

            ((22, 11), FILTER, 'upgrade'): 28,
            ((21, 10), FILTER, 'upgrade'): 27,
            ((20, 9), FILTER, 'upgrade'): 26,

            ((24, 12), DESTRUCTOR, 'upgrade'): 25,
            ((26, 12), DESTRUCTOR, 'upgrade'): 24.5
            ((15, 4), DESTRUCTOR, 'upgrade'): 24,
            

            ((23, 11), ENCRYPTOR, 'spawn'): 23,
            ((23, 11), ENCRYPTOR, 'upgrade'): 22,
            ((22, 10), ENCRYPTOR, 'spawn'): 21,
            ((22, 10), ENCRYPTOR, 'upgrade'): 20,
            ((21, 9), ENCRYPTOR, 'spawn'): 19,
            ((21, 9), ENCRYPTOR, 'upgrade'): 18
        }

        # right_side_base_passive_defense_to_priority = {
        #     ((27 - x, y), firewall_type, action): priority \
        #     for (((x, y), firewall_type, action), priority) \
        #     in left_side_base_passive_defense_to_priority.items()
        # }



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
        Stops when we have num_cores_to_leave CORES remaining UNLESS we need
        to deploy our high priority filters. THEN WE VIOLATE THIS!
        '''
        priority_sorted_passive_defense = [defense for defense, priority \
            in sorted(self.actual_passive_defense_to_priority.items(), \
            key=lambda item: item[1], reverse=True) if priority > 0]
        for location, firewall_unit_type, action in priority_sorted_passive_defense:
            if game_state.get_resource(CORES) - game_state.type_cost(firewall_unit_type)[CORES] < num_cores_to_leave:
                # Ok this is janky but we want to ensure that we have at least
                # our basic filters set up. I have seen games where the opponent
                # demolished our defense and though we had enough cores to
                # build back our filters, we left it out because we limited ourselves.
                # And that made a big difference in points (since it leaves a gap in our
                # defense and the opponent units will target that now)
                break
                # minimum_priority_to_fulfill = self.actual_passive_defense_to_priority[((10, 6), FILTER, 'spawn')]
                # cur_priority = self.actual_passive_defense_to_priority[(location, firewall_unit_type, action)]
                # if cur_priority < minimum_priority_to_fulfill:
                #     break
                # Otherwise continue and violate our num_cores_to_leave!!
                # Note that this can cause big issues esp. if we are attacking
                # but those issues are likely worse if we don't patch our filters
            if action == 'spawn':
                num_units = game_state.attempt_spawn(firewall_unit_type, list(location))
            elif action == 'upgrade':
                num_units = game_state.attempt_upgrade(list(location))
            else:
                raise ValueError("Action must be 'spawn' or 'upgrade'")
            # Could use num_units, which shows whether the spawn or upgrade happened but nah
