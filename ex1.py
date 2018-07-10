import search
import random
import math
import copy
from random import randint

GRID_LIMIT = 0


class SpaceshipProblem(search.Problem):
    """This class implements a spaceship problem"""

    def __init__(self, initial):
        """Don't forget to set the goal or implement the goal test
        You should change the initial to your own representation"""
        search.Problem.__init__(self, initial)

    def check_straight_line(self,ship_name, target, spaceships):
        for name, location in spaceships:
            if ship_name == name:
                if (location[0] == target[0] and location[1] == target[1] and location[2] !=
                        target[2]):
                    return 2
                elif (location[0] == target[0] and location[1] != target[1] and location[2] ==
                      target[2]):
                    return 1
                elif(location[0] != target[0] and location[1] == target[1] and location[2] ==
                     target[2]):
                    return 0
                else:
                    return -1

    def check_no_ships_in_location(self, spaceships, new_location):
        for ship, location in spaceships:
            if location == new_location:
                return False
        return True

    def check_no_targets_on_way(self,ship_name , target_location, diff_coordinate, all_targets,ships):
        for sname, location in ships:
            if sname == ship_name:
                if diff_coordinate == 0:
                    for target in all_targets:
                        if ((target[1] == location[1]) and (target[2] == location[2])):
                            if ((target[0] > location[0] and target[0] < target_location[0]) or (
                                    target[0] < location[0] and target[0] > target_location[0])):
                                return False
                elif diff_coordinate == 1:
                    for target in all_targets:
                        if ((target[0] == location[0]) and (target[2] == location[2])):
                            if ((target[1] > location[1] and target[1] < target_location[1]) or (
                                    target[1] < location[1] and target[1] > target_location[1])):
                                return False
                elif diff_coordinate == 2:
                    for target in all_targets:
                        if ((target[0] == location[0]) and (target[1] == location[1])):
                            if ((target[2] > location[2] and target[2] < target_location[2]) or (
                                    target[2] < location[2] and target[2] > target_location[2])):
                                return False
                return True


    def actions(self, state):
        """Return the actions that can be executed in the given
        state. The result would typically be a tuple, but if there are
        many actions, consider yielding them one at a time in an
        iterator, rather than building them all at once."""

        actions = ()
        spaceships = state[0] #tuple of: (ShipName, Location)
        instruments = state[1] #tuple of: (ShipName, DeviceName, Power, Calibrated, CalibrationTarget, FinalTarget,Hit)
        all_targets = state[2]

        for ship_name, device_name, power, cali, cali_target, hit_target, hit_flag in instruments:
            if hit_flag == 0: #target wasn't hit so far
                if power == 0 or cali == 0:
                    diff_coord = self.check_straight_line(ship_name, cali_target, spaceships)
                    no_targets_in_way = self.check_no_targets_on_way(ship_name, cali_target, diff_coord, all_targets,spaceships)
                    if diff_coord != -1 and no_targets_in_way:
                        #straight line and no targets nor ships on the way
                        if power == 0:
                            #################turn on device################
                            act = ("turn_on", ship_name, device_name)
                            if act not in actions:
                                actions = (act,) + actions
                        elif power == 1 and cali == 0:
                            act = ("calibrate", ship_name, device_name, cali_target)
                            if act not in actions:
                                actions = (act,) + actions
                    else:
                        #no straight line, need to move the spaceship
                        for ship , location in spaceships:
                            if ship == ship_name:
                                ##############move####################
                                # move spaceship according to spaceship current location (x,y,z) and GRID_LIMIT
                                if (location[0] + 1 < GRID_LIMIT):
                                    # x move up
                                    # x coordinate within grid
                                    move_to = (location[0] + 1, location[1], location[2])
                                    if ((move_to not in all_targets) and (
                                    self.check_no_ships_in_location(spaceships, move_to))):
                                        act = ("move", ship, location, move_to)
                                        actions = (act,) + actions
                                if (location[0] - 1 >= 0):
                                    # x move down
                                    move_to = (location[0] - 1, location[1], location[2])
                                    if ((move_to not in all_targets) and (
                                    self.check_no_ships_in_location(spaceships, move_to))):
                                        act = ("move", ship, location, move_to)
                                        actions = (act,) + actions

                                if (location[1] + 1 < GRID_LIMIT):
                                    # y move up
                                    # y coordinate within grid
                                    move_to = (location[0], location[1] + 1, location[2])
                                    if ((move_to not in all_targets) and (
                                    self.check_no_ships_in_location(spaceships, move_to))):
                                        act = ("move", ship, location, move_to)
                                        actions = (act,) + actions
                                if (location[1] - 1 >= 0):
                                    # y move down
                                    move_to = (location[0], location[1] - 1, location[2])
                                    if ((move_to not in all_targets) and (
                                    self.check_no_ships_in_location(spaceships, move_to))):
                                        act = ("move", ship, location, move_to)
                                        actions = (act,) + actions

                                if (location[2] + 1 < GRID_LIMIT):
                                    # z move up
                                    # z coordinate within grid
                                    move_to = (location[0], location[1], location[2] + 1)
                                    if ((move_to not in all_targets) and (
                                    self.check_no_ships_in_location(spaceships, move_to))):
                                        act = ("move", ship, location, move_to)
                                        actions = (act,) + actions
                                if (location[2] - 1 >= 0):
                                    # z move down
                                    move_to = (location[0], location[1], location[2] - 1)
                                    if ((move_to not in all_targets) and (
                                    self.check_no_ships_in_location(spaceships, move_to))):
                                        act = ("move", ship, location, move_to)
                                        actions = (act,) + actions
                elif power == 1 and cali == 1:
                    diff_coord = self.check_straight_line(ship_name, hit_target, spaceships)
                    no_targets_in_way = self.check_no_targets_on_way(ship_name, hit_target, diff_coord, all_targets,spaceships)
                    if diff_coord != -1 and no_targets_in_way:
                        act = ("use", ship_name, device_name, hit_target)
                        actions = (act,) + actions
                    else:
                        #no straight line or there are ship or targets in the way to the hit target, need to move
                        for ship , location in spaceships:
                            if ship == ship_name:
                                ##############move####################
                                # move spaceship according to spaceship current location (x,y,z) and GRID_LIMIT
                                if (location[0] + 1 < GRID_LIMIT):
                                    # x move up
                                    # x coordinate within grid
                                    move_to = (location[0] + 1, location[1], location[2])
                                    if ((move_to not in all_targets) and (
                                    self.check_no_ships_in_location(spaceships, move_to))):
                                        act = ("move", ship, location, move_to)
                                        actions = (act,) + actions
                                if (location[0] - 1 >= 0):
                                    # x move down
                                    move_to = (location[0] - 1, location[1], location[2])
                                    if ((move_to not in all_targets) and (
                                    self.check_no_ships_in_location(spaceships, move_to))):
                                        act = ("move", ship, location, move_to)
                                        actions = (act,) + actions

                                if (location[1] + 1 < GRID_LIMIT):
                                    # y move up
                                    # y coordinate within grid
                                    move_to = (location[0], location[1] + 1, location[2])
                                    if ((move_to not in all_targets) and (
                                    self.check_no_ships_in_location(spaceships, move_to))):
                                        act = ("move", ship, location, move_to)
                                        actions = (act,) + actions
                                if (location[1] - 1 >= 0):
                                    # y move down
                                    move_to = (location[0], location[1] - 1, location[2])
                                    if ((move_to not in all_targets) and (
                                    self.check_no_ships_in_location(spaceships, move_to))):
                                        act = ("move", ship, location, move_to)
                                        actions = (act,) + actions

                                if (location[2] + 1 < GRID_LIMIT):
                                    # z move up
                                    # z coordinate within grid
                                    move_to = (location[0], location[1], location[2] + 1)
                                    if ((move_to not in all_targets) and (
                                    self.check_no_ships_in_location(spaceships, move_to))):
                                        act = ("move", ship, location, move_to)
                                        actions = (act,) + actions
                                if (location[2] - 1 >= 0):
                                    # z move down
                                    move_to = (location[0], location[1], location[2] - 1)
                                    if ((move_to not in all_targets) and (
                                    self.check_no_ships_in_location(spaceships, move_to))):
                                        act = ("move", ship, location, move_to)
                                        actions = (act,) + actions

        return actions

    def result(self, state, action):
        # actions_start = time.time()
        """Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state)."""

        new_state = copy.deepcopy(state)
        spaceships = new_state[0]  # tuple of: (ShipName, Location)
        devices = new_state[1]  # tuple of: (ShipName, DeviceName, Power, Calibrated, CalibrationTarget,FinalTarget, Hit)
        all_targets = new_state[2]


        if action[0] == "move":
        #act = ("move", ship_name, location, move_to)
            stemplist = [list(x) for x in spaceships]
            for ship in stemplist:
                if ship[0] == action[1]:
                        if ship[1] == action[2]:
                            ship[1] = action[3]
            spaceships = tuple([tuple(x) for x in stemplist])

        elif action[0] == "turn_on":
        #act = ("turn_on", ship_name, device_name)
        #devices is a tuple of: (ShipName, DeviceName, Power, Calibrated, CalibrationTarget, FinalTarget,Hit)
            dtemplist = [list(x) for x in devices]
            for device in dtemplist:
                if device[0] == action[1] and device[1] == action[2]:
                    device[2] = 1
                elif device[0] == action[1] and device[1] != action[2]:
                    device[2] = 0
                    device[3] = 0
            devices = tuple([tuple(x) for x in dtemplist])


        elif action[0] == "calibrate":
        #act = ("calibrate", ship_name, device_name, cali_target)
            dtemplist = [list(x) for x in devices]
            for device in dtemplist:
                if device[0] == action[1] and device[1] == action[2]:
                    device[3] = 1
            devices = tuple([tuple(x) for x in dtemplist])

        elif action[0] == "use":
        #act = ("use", ship_name, device_name, hit_target)
            dtemplist = [list(x) for x in devices]
            for device in dtemplist:
                if device[0] == action[1] and device[1] == action[2] and device[5] == action[3]:
                    device[6] = 1
            devices = tuple([tuple(x) for x in dtemplist])

        new_state = (spaceships,devices,all_targets)
        #actions_finish = time.time()
        # print(actions_finish-actions_start)
        return (new_state)

    def goal_test(self, state):
        """ Given a state, checks if this is the goal state, compares to the created goal state"""
        devices = state[1]
        for d in devices:
            if d[6] == 0:
                return False
        return True


    def h(self, node):
        """ This is the heuristic. It gets a node (not a state,
        state can be accessed via node.state)
        and returns a goal distance estimate"""

        devices = node.state[1]
        ships = node.state[0]
        c = 0
        for ship_name, device_name, power, cali, cali_target, hit_target, hit in devices:
            if hit == 0:
                if power == 0:
                    for sname, slocation in ships:
                        if sname == ship_name:
                            cali_routh_len = abs(slocation[0] - cali_target[0]) + abs(slocation[1] - cali_target[1]) + abs(slocation[2] - cali_target[2])
                            hit_routh_len = abs(cali_target[0] - hit_target[0]) + abs(cali_target[1] - hit_target[1]) + abs(cali_target[2] - hit_target[2])
                            c += cali_routh_len + hit_routh_len
                    c += 3
                elif power == 1 and cali == 0:
                    for sname, slocation in ships:
                        if sname == ship_name:
                            cali_routh_len = abs(slocation[0] - cali_target[0]) + abs(slocation[1] - cali_target[1]) + abs(slocation[2] - cali_target[2])
                            hit_routh_len = abs(cali_target[0] - hit_target[0]) + abs(cali_target[1] - hit_target[1]) + abs(cali_target[2] - hit_target[2])
                            c += cali_routh_len + hit_routh_len
                    c += 2
                elif power == 1 and cali == 1:
                    for sname, slocation in ships:
                        if sname == ship_name:
                            hit_routh_len = abs(slocation[0] - hit_target[0]) + abs(slocation[1] - hit_target[1]) + abs(slocation[2] - hit_target[2])
                            c += hit_routh_len
                    c += 1
        return (c)

def create_spaceship_problem(problem, goal):
    global GRID_LIMIT

    #problem is a tuple of all the input
    GRID_LIMIT = problem[0]

    spaceships=() #tuple of: (ShipName, Location)
    devices = () #tuple of: (ShipName, DeviceName, Power, Calibrated, CalibrationTarget, FinalTarget,Hit)
    all_targets = ()

    for ship_name in problem[1]:
        #creating spaceships tuple
        ship_starting_location = problem[6][ship_name]  # get ships location
        new_ship = (ship_name,ship_starting_location)
        spaceships = (new_ship,) + spaceships

        #creating devices tuple
        all_devices = problem[3][ship_name]  # get ships devices
        for device_name in all_devices:
            device_calib = problem[4][device_name]

            #####creating all targets tuple###
            if device_calib not in all_targets:
                all_targets = (device_calib,) + all_targets

            for key in problem[5]:
                if key not in all_targets:
                    all_targets = (key,) + all_targets
            #################################

                values = problem[5][key]
                if device_name in values:
                    new_device = (ship_name, device_name, 0, 0, device_calib,key,0)
                    devices = (new_device,) + devices


    problem = (spaceships,devices,all_targets)
    return SpaceshipProblem(problem)
