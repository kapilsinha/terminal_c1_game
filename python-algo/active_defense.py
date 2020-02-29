import copy
import math
import random

from blockade import Blockade
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

        self.blockade = Blockade(config)

    def deploy_units(self, game_state, num_scramblers=None):
        '''
        Deploys scramblers in specific locations
        '''
        if num_scramblers is None:
            num_scramblers = self.num_scramblers_to_deploy(game_state)
        self.better_scrambler_deploy_strategy(game_state, num_scramblers)

    def basic_scrambler_deploy_strategy(self, game_state, num_scramblers):
        '''
        Basic strategy: Just deploy all the scramblers alternating at (8, 5) and (19, 5)
        Locations are somewhat arbitrary but based on playing the game, seem good
        '''
        left_deploy_location = [11, 2]
        right_deploy_location = [16, 2]
        num_deployed_on_left_side = num_scramblers // 2
        num_deployed_on_right_side = num_scramblers - num_deployed_on_left_side

        priorities = [[13,0], [14,0], [20,6], [13,0]]

        for i in range(num_scramblers):
            game_state.attempt_spawn(SCRAMBLER, priorities[i], num=1)

        # if random.random() < .5:
        #     # Swap em randomly to keep things interestings
        #     num_deployed_on_left_side, num_deployed_on_right_side = num_deployed_on_right_side, num_deployed_on_left_side
        # game_state.attempt_spawn(SCRAMBLER, left_deploy_location, num=num_deployed_on_left_side)
        # game_state.attempt_spawn(SCRAMBLER, right_deploy_location, num=num_deployed_on_right_side)

    def better_scrambler_deploy_strategy(self, game_state, num_scramblers):
        '''
        If 2 or fewer scramblers are required, just resort to basic scrambler strategy
        Otherwise, split between sending scramblers through the center (basic strategy) and
        sending to a single side
        (we could implement logic to send only to a single side but for now
         we send to both)
        Can't think of a better way to do this so always send num_scramblers // 2
        down the sides and the rest down the center
        TODO: Factor in opponent move history to make this decision?

        NOTE: Actually at this point since we are largely guessing which side
        the opponent will deploy, we might as well incorporate inherent asymmetry
        in our passive defense (e.g. guard the right side better with destructors
        and deploy scramblers on the left side) - but enemy EMPs could mow down our destructors
        '''
        if num_scramblers <= 2:
            self.basic_scrambler_deploy_strategy(game_state, num_scramblers)
            return

        num_scramblers_to_deploy_on_side = num_scramblers // 2
        num_scramblers_to_deploy_on_center = num_scramblers - num_scramblers_to_deploy_on_side

        num_scramblers_to_deploy_on_left = num_scramblers_to_deploy_on_side 
        # num_scramblers_to_deploy_on_right = num_scramblers_to_deploy_on_side - num_scramblers_to_deploy_on_left
        # if random.random() < .5:
        #     num_scramblers_to_deploy_on_left, num_scramblers_to_deploy_on_right \
        #         = num_scramblers_to_deploy_on_right, num_scramblers_to_deploy_on_left

        self.basic_scrambler_deploy_strategy(game_state, num_scramblers_to_deploy_on_center)
        self.deploy_scramblers_on_left_side(game_state, num_scramblers_to_deploy_on_left)
        # self.deploy_scramblers_on_right_side(game_state, num_scramblers_to_deploy_on_right)


    def deploy_scramblers_on_left_side(self, game_state, num_scramblers):
        '''
        Deploys scramblers on left side, in hopes that it protect it
        in case the opponent targets that side (esp. with many pings). Of course,
        we blockade left to force our scrambler to go left.

        Quite some thought has gone into this:
        Assume the opponent deploys many pings at (or very near) [14, 27] to get
        a quick attack on our left side.

        I want our scramblers to just reach [2, 11] when the opponent's pings
        just reach [2, 15]. Their pings reach [2, 15] in 24 steps.
        Thus we start our scramblers at [5, 8] so it reaches [2, 11] in 24 frames.

        (Note that we prefer for our scramblers to be at [2, 12] when the opponent's
        pings are at [3, 16] but the opponent's pings arrive there in 22 frames
        and scramblers move once every 4 frames so this is less effective
        -> 4 does not divide 22)
        '''
        if num_scramblers == 0:
            # Good check to make sure we don't unnecessarily blockade if we don't
            # need to deploy scramblers on this side
            return

        priorities = [[5,8], [7,6], [6,7]]
        self.blockade.blockade_left(game_state)



        for i in range(num_scramblers):
            game_state.attempt_spawn(SCRAMBLER, priorities[i], num=1)

    # def deploy_scramblers_on_right_side(self, game_state, num_scramblers):
    #     '''
    #     See the comment for deploy_scrambler_on_left_side
    #     '''
    #     if num_scramblers == 0:
    #         # Good check to make sure we don't unnecessarily blockade if we don't
    #         # need to deploy scramblers on this side
    #         return
    #     self.blockade.cheap_blockade_right(game_state)
    #     game_state.attempt_spawn(SCRAMBLER, [22, 8], num=num_scramblers)

    def num_scramblers_to_deploy(self, game_state):
        '''
        num_scramblers_to_deploy = ceil[opponent_bits / 4]
        = (opponent_bits + 3) // 4
        '''
        return ((enemy_num_bits // 3) + 1) // 2 + 1
