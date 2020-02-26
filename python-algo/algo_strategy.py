import json
import math
import random
from sys import maxsize
import warnings

import gamelib
from passive_defense import PassiveDefense
from active_defense import ActiveDefense
from attack import Attack

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips:

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical
  board states. Though, we recommended making a copy of the map to preserve
  the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """
        Read in config and perform any initial setup here
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, BITS, CORES
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]
        BITS = 1
        CORES = 0
        # This is a good place to do initial setup
        self.previous_turn_scored_on_locations = []
        self.scored_on_locations = []
        # Active move can be 'active_defense', 'attack_center', 'attack_left', 'attack_right'
        self.active_move = 'active_defense'
        self.passive_defense = PassiveDefense(config)
        self.active_defense = ActiveDefense(config)
        self.attack = Attack(config)


    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Comment or remove this line to enable warnings.

        self.starter_strategy(game_state)
        game_state.submit_turn()


    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some Scramblers early on.
        We will place destructors near locations the opponent managed to score on.
        For offense we will use long range EMPs if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Pings to try and score quickly.
        """
        # 1. Update passive defense priorities based on game state
        self.dynamic_update_defences(game_state)
        if self.active_move == 'attack':
            # Do special update of defense priorities
            self.attack.compute_attack_type(game_state)
            self.attack.update_passive_defense(game_state, self.passive_defense)

        # 2. Place passive defenses
        # THERE MUST BE 2 cores if in attack (hard-coded necessity in blockade)
        # and there MUST BE 1 core if in active defense (to do side scrambler strategy)
        if self.active_move == 'attack':
            num_cores_to_leave = 2
        elif game_state.turn_number < 5:
            num_cores_to_leave = 0
        else:
            # Carefully set so that 3 + 5 = 8 = 4 (encryptor cost) + 4 (cost of adding back side filters)
            num_cores_to_leave = 3
        self.passive_defense.deploy_units(game_state, num_cores_to_leave)

        # 3. Deploy active defense or attack units
        if self.active_move == 'active_defense':
            # Special handling of turn 1 to deploy all scramblers to protect the
            # unguarded middle area. Deliberately chose these locations so that
            # the scramblers remain clustered for more time (and can still take
            # out pings in frame 24 or so if that's what the opponent sends)
            if game_state.turn_number < 1:
                game_state.attempt_spawn(SCRAMBLER, [6, 7], num=2)
                game_state.attempt_spawn(SCRAMBLER, [21, 7], num=3)
            else:
                self.active_defense.deploy_units(game_state)
        elif self.active_move == 'attack':
            self.attack.deploy_units(game_state)
        else:
            raise ValueError("Active move must be attack or active defense")

        # 4. Prep for next turn
        self.prep_for_next_turn(game_state)

    def dynamic_update_defences(self, game_state):
        """
        A) Update passive defense priorities to better cover 'weak' areas.
        B) Also removes stationary units with low health (the thinking here is that
           we remove it now and if it is high priority, it will be re-added next
           round, so that opponents can't just easily penetrate low health firewalls)
        A weak area means it is near one of the following:
        1. A location where the opponent scored on us
        2. A location where our firewall health is low
        # TODO: Item 3 below. Not sure if it's worth?
        3. A location that is likely (given an arbitrary opponent's starting location)
           to be the first location that is attacked in the opponent's path
        """
        # 1. If the opponent just scored on us, increase the priority in the area
        # where they scored and do nothing else.
        if len(self.previous_turn_scored_on_locations) > 0:
            gamelib.debug_write("Fortifying the area where opponent just scored on us")
            increase_priority_amount = 10 # arbitrary, requires testing
            circle_radius = 4.5
            locations = [tuple(loc) for loc in self.previous_turn_scored_on_locations]
            most_scored_location = max(set(locations), key = locations.count)
            self.passive_defense.increase_priority_near_location(
                game_state.game_map, most_scored_location, circle_radius, increase_priority_amount
            )
            return

        # 2. Remove firewalls that have less than THRESHOLD of their health remaining
        # Also find the firewall that has the lowest health ratio (if it is < 1)
        # and increase the priority in the area
        stationary_unit_location_to_health_ratio = game_state.get_stationary_unit_location_to_health_ratio()
        health_ratio_threshold = 0.6
        for location, health_ratio in stationary_unit_location_to_health_ratio.items():
            if health_ratio < health_ratio_threshold:
                gamelib.debug_write("Removed stationary unit at location {} due to low health; its health ratio was {}" \
                    .format(location, health_ratio))
                game_state.attempt_remove(location)
        if len(stationary_unit_location_to_health_ratio) == 0:
            min_health_location = None
            min_health_ratio = 1
        else:
            min_health_location, min_health_ratio = min(
                stationary_unit_location_to_health_ratio.items(), key=lambda x: x[1])
        if min_health_ratio < 1:
            # The unit is damaged
            increase_priority_amount = 3 # arbitrary, requires testing
            circle_radius = 2
            gamelib.debug_write(f"Fortifying the area around {min_health_location} due to low firewall health")
            self.passive_defense.increase_priority_near_location(
                game_state.game_map, min_health_location, circle_radius, increase_priority_amount
            )

    def stall_with_scramblers(self, game_state):
        """
        Send out Scramblers at random locations to defend our base from enemy moving units.
        Unused (this was part of the starter code)
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) + game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT)

        # Remove locations that are blocked by our own firewalls
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)

        # While we have remaining bits to spend lets send out scramblers randomly.
        while game_state.get_resource(BITS) >= game_state.type_cost(SCRAMBLER)[BITS] and len(deploy_locations) > 0:
            # Choose a random deploy location.
            deploy_index = random.randint(0, len(deploy_locations) - 1)
            deploy_location = deploy_locations[deploy_index]

            game_state.attempt_spawn(SCRAMBLER, deploy_location)
            """
            We don't have to remove the location since multiple information
            units can occupy the same space.
            """

    def emp_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our EMP's can attack from long range.
        Unused (this was part of the starter code)
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [FILTER, DESTRUCTOR, ENCRYPTOR]
        cheapest_unit = FILTER
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost[game_state.BITS] < gamelib.GameUnit(cheapest_unit, game_state.config).cost[game_state.BITS]:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our EMPs from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn EMPs next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(EMP, [24, 10], 1000)

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at: https://docs.c1games.com/json-docs.html
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        #if len(events['spawn']) > 0: # use this to create the history
            # I think it is (location, unit_type, _, player_number)?
            #gamelib.debug_write(state["turnInfo"])
            #gamelib.debug_write(events)
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly,
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                gamelib.debug_write("Got scored on at: {}".format(location))
                self.previous_turn_scored_on_locations.append(location)
                self.scored_on_locations.append(location)
                gamelib.debug_write("All locations: {}".format(self.scored_on_locations))

    def prep_for_next_turn(self, game_state):
        '''
        Choose active defense if num_bits_in_next_round < 6 + num_bits_earned_per_round
        Choose to attack in next turn if num_bits_in_next_round > 11 + num_bits_earned_per_round
        Randomly choose active defense or attack (in weighted fashion) in between
        ^ We can do the above by a single random number comparison

        Set relevant variables based on whatever active move is chosen
        '''
        num_bits_in_next_round = game_state.project_future_bits()
        if num_bits_in_next_round > random.randint(
            11 + game_state.turn_number // 10, 16 + game_state.turn_number // 10):
            self.active_move = 'attack'
        else:
            self.active_move = 'active_defense'

        # If we choose active defense, reset passive defense priorities.
        # Otherwise don't because we may have deliberately adjusted priorities
        # for the attack next move and don't want that to be reset
        if self.active_move == 'active_defense':
            self.passive_defense.reset_passive_defense_priority(game_state)
        elif self.active_move == 'attack':
            # Delete edge filters if active_move is attack
            # (the filters may or may not be added back in the next round,
            # depending on whether we attack on that side)
            # Also temporarily change their priority to 0 so they don't get re-added
            left_filter_location = [1, 13]
            right_filter_location = [26, 13]
            game_state.attempt_remove([left_filter_location, right_filter_location])
            side_filter_priority_overrides = {(tuple(left_filter_location), FILTER, 'spawn'): 0,
                                              (tuple(right_filter_location), FILTER, 'spawn'): 0}
            self.passive_defense.set_passive_defense_priority_overrides(side_filter_priority_overrides)
        else:
            raise ValueError("active_move must be active_defense or attack")

        # Clear out previous turn details
        self.previous_turn_scored_on_locations = []

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
