import time
import random
from utils import (
    is_in, argmin, argmax, argmax_random_tie, probability, weighted_sampler,
    memoize, print_table, open_data, Stack, FIFOQueue, PriorityQueue, name,
    distance
)
from collections import defaultdict
import math
import sys
import bisect
import copy
infinity = float('inf')


GRID_LIMIT = 0
STEPS = 0
lasers_locations = ()
edge_locations = ()

#######################################################################
##from search.py
class Problem(object):

    """The abstract class for a formal problem.  You should subclass
    this and implement the methods actions and result, and possibly
    __init__, goal_test, and path_cost. Then you will create instances
    of your subclass and solve them with the various search functions."""

    def __init__(self, initial, goal=None):
        """The constructor specifies the initial state, and possibly a goal
        state, if there is a unique goal.  Your subclass's constructor can add
        other arguments."""
        self.initial = initial
        self.goal = goal

    def actions(self, state):
        """Return the actions that can be executed in the given
        state. The result would typically be a list, but if there are
        many actions, consider yielding them one at a time in an
        iterator, rather than building them all at once."""
        raise NotImplementedError

    def result(self, state, action):
        """Return the state that results from executing the given
        action in the given state. The action must be one of
        self.actions(state)."""
        raise NotImplementedError

    def goal_test(self, state):
        """Return True if the state is a goal. The default method compares the
        state to self.goal or checks for state in self.goal if it is a
        list, as specified in the constructor. Override this method if
        checking against a single self.goal is not enough."""
        if isinstance(self.goal, list):
            return is_in(state, self.goal)
        else:
            return state == self.goal

    def path_cost(self, c, state1, action, state2):
        """Return the cost of a solution path that arrives at state2 from
        state1 via action, assuming cost c to get up to state1. If the problem
        is such that the path doesn't matter, this function will only look at
        state2.  If the path does matter, it will consider c and maybe state1
        and action. The default method costs 1 for every step in the path."""
        return c + 1

    def value(self, state):
        """For optimization problems, each state has a value.  Hill-climbing
        and related algorithms try to maximize this value."""
        raise NotImplementedError
# ______________________________________________________________________________

class Node:

    """A node in a search tree. Contains a pointer to the parent (the node
    that this is a successor of) and to the actual state for this node. Note
    that if a state is arrived at by two paths, then there are two nodes with
    the same state.  Also includes the action that got us to this state, and
    the total path_cost (also known as g) to reach the node.  Other functions
    may add an f and h value; see best_first_graph_search and astar_search for
    an explanation of how the f and h values are handled. You will not need to
    subclass this class."""

    def __init__(self, state, parent=None, action=None, path_cost=0):
        """Create a search tree Node, derived from a parent by an action."""
        self.state = state
        self.parent = parent
        self.action = action
        self.path_cost = path_cost
        self.depth = 0
        if parent:
            self.depth = parent.depth + 1

    def __repr__(self):
        return "<Node {}>".format(self.state)

    def __lt__(self, node):
        return self.state < node.state

    def expand(self, problem):
        """List the nodes reachable in one step from this node."""
        return [self.child_node(problem, action)
                for action in problem.actions(self.state)]

    def child_node(self, problem, action):
        """[Figure 3.10]"""
        next = problem.result(self.state, action)
        return Node(next, self, action,
                    problem.path_cost(self.path_cost, self.state,
                                      action, next))

    def solution(self):
        """Return the sequence of actions to go from the root to this node."""
        return [node.action for node in self.path()[1:]]

    def path(self):
        """Return a list of nodes forming the path from the root to this node."""
        node, path_back = self, []
        while node:
            path_back.append(node)
            node = node.parent
        return list(reversed(path_back))

    # We want for a queue of nodes in breadth_first_search or
    # astar_search to have no duplicated states, so we treat nodes
    # with the same state as equal. [Problem: this may not be what you
    # want in other contexts.]

    def __eq__(self, other):
        return isinstance(other, Node) and self.state == other.state

    def __hash__(self):
        return hash(self.state)

# ______________________________________________________________________________
# Uninformed Search algorithms

def graph_search(problem, frontier):
    """Search through the successors of a problem to find a goal.
    The argument frontier should be an empty queue.
    If two paths reach a state, only use the first one. [Figure 3.7]"""
    frontier.append(Node(problem.initial))
    explored = set()
    while frontier:
        node = frontier.pop()
        if problem.goal_test(node.state):
            return node
        explored.add(node.state)
        frontier.extend(child for child in node.expand(problem)
                        if child.state not in explored and
                        child not in frontier)
    return None

def best_first_graph_search(problem, f):
    """Search the nodes with the lowest f scores first.
    You specify the function f(node) that you want to minimize; for example,
    if f is a heuristic estimate to the goal, then we have greedy best
    first search; if f is node.depth then we have breadth-first search.
    There is a subtlety: the line "f = memoize(f, 'f')" means that the f
    values will be cached on the nodes as they are computed. So after doing
    a best first search you can examine the f values of the path returned."""
    f = memoize(f, 'f')
    node = Node(problem.initial)
    if problem.goal_test(node.state):
        return node
    frontier = PriorityQueue(min, f)
    frontier.append(node)
    explored = set()
    while frontier:
        node = frontier.pop()
        if problem.goal_test(node.state):
            return node
        explored.add(node.state)
        for child in node.expand(problem):
            if child.state not in explored and child not in frontier:
                frontier.append(child)
            elif child in frontier:
                incumbent = frontier[child]
                if f(child) < f(incumbent):
                    del frontier[incumbent]
                    frontier.append(child)
    return None
# ______________________________________________________________________________
class SpaceshipController:
    "This class is a controller for a spaceship problem."

    def __init__(self, problem, initial_state):
        """Initialize controller for given the initial setting.
        This method MUST terminate within the specified timeout."""
        global GRID_LIMIT
        self.nb_steps = problem[8]
        GRID_LIMIT = problem[0]
        spaceships = ()  # tuple of: (ShipName, Location)
        devices = ()  # tuple of: (ShipName, DeviceName, Power, Calibrated, CalibrationTarget, FinalTarget,Hit)
        all_targets = ()
        global lasers_locations
        global edge_locations

        #add locations in lasers
        for location in problem[7]:
            if location[0] == -1:
                for i in range(GRID_LIMIT):
                    l = (i, location[1], location[2])
                    lasers_locations = (l,) + lasers_locations
            if location[1] == -1:
                for i in range(GRID_LIMIT):
                    l = (location[0], i, location[2])
                    lasers_locations = (l,) + lasers_locations
            if location[2] == -1:
                for i in range(GRID_LIMIT):
                    l = (location[0], location[1], i)
                    lasers_locations = (l,) + lasers_locations

        #add edges to dangerous locations
        #x
        for y in range(GRID_LIMIT):
            for z in range(GRID_LIMIT):
                l = (0,y,z)
                t = (GRID_LIMIT-1,y,z)
                edge_locations = (l,) + edge_locations
                edge_locations = (t,) + edge_locations
        #y
        for x in range(GRID_LIMIT):
            for z in range(GRID_LIMIT):
                l = (x,0,z)
                t = (x,GRID_LIMIT-1,z)
                if l not in edge_locations:
                    edge_locations = (l,) + edge_locations
                if t not in edge_locations:
                    edge_locations = (t,) + edge_locations
        #z
        for x in range(GRID_LIMIT):
            for y in range(GRID_LIMIT):
                l = (x,y,0)
                t = (x,y,GRID_LIMIT-1)
                if l not in edge_locations:
                    edge_locations = (l,) + edge_locations
                if t not in edge_locations:
                    edge_locations = (t,) + edge_locations

        for ship_name in problem[1]:
            # creating spaceships tuple
            ship_starting_location = problem[6][ship_name]  # get ships location
            new_ship = (ship_name, ship_starting_location)
            spaceships = (new_ship,) + spaceships
            # creating devices tuple
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
                        new_device = (ship_name, device_name, 0, 0, device_calib, key, 0)
                        devices = (new_device,) + devices
        self.my_world = (spaceships, devices, all_targets)
        self.original_world = (spaceships,devices,all_targets)

        ##########################
        # running GBFS from current world
        p = SpaceshipProblem(self.my_world)
        self.timeout = problem[9]
        r = check_problem(p, (lambda p: best_first_graph_search(p, p.h)), self.timeout)
        ##########################

        self.gbfs_route = copy.deepcopy(r[2])
        self.last_action = ()
        self.original_gbfs = copy.deepcopy(r[2])

    def choose_next_action(self, state):
        """Choose next action for driverlog controller given the current state.
        Action should be returned in the format described previous parts of the project"""
        global STEPS
        STEPS+=1
        spaceships = self.my_world[0]
        devices = self.my_world[1]
        all_targets = self.my_world[2]

        active_ships = state[0]
        ships_positions = state[1]

        #remove exploded ships
        for ship in spaceships:
            if ship[0] not in ships_positions:
                temp_list = list(spaceships)
                temp_list.remove(ship)
                spaceships = tuple(temp_list)
        for device in devices:
            if device[0] not in ships_positions:
                temp_list = list(devices)
                temp_list.remove(device)
                devices = tuple(temp_list)
        self.my_world = (spaceships, devices, all_targets)

        #all ships exploded
        if not devices or not spaceships:
            if STEPS < self.nb_steps:
                next_action = ("reset",)
                self.my_world = (self.original_world[0], self.original_world[1], self.original_world[2])
                self.gbfs_route = self.original_gbfs
                self.last_action = ()
                return (next_action)


        #first run or after reset
        if not self.last_action:
            next_action = self.gbfs_route[0]
            self.last_action = next_action
            del self.gbfs_route[0]
            self.update_my_world(next_action)
            return next_action



        #check to see it the place where the spaceship suppose to be is the place where it is located
        if self.last_action[0] == "move":
            if self.last_action[1] in ships_positions:
                if tuple(ships_positions[self.last_action[1]]) == self.last_action[3]:
                    if not self.gbfs_route:
                        next_action = ("turn_on", devices[0][0],devices[0][1])
                        self.last_action = next_action
                        return next_action

                    next_action = self.gbfs_route[0]
                    self.last_action = next_action
                    del self.gbfs_route[0]
                    self.update_my_world(next_action)
                    return next_action
                else:
                    # update my world with the current state
                    for ship in spaceships:
                        if ship[0] == self.last_action[1]:
                            current_location = tuple(ships_positions[ship[0]])
                            action = ("move", ship[0], ship[1], current_location)
                            self.update_my_world(action)
        else:
            if not self.gbfs_route:
                next_action = ("turn_on", devices[0][0], devices[0][1])
                self.last_action = next_action
                return next_action

            next_action = self.gbfs_route[0]
            self.last_action = next_action
            del self.gbfs_route[0]
            self.update_my_world(next_action)
            return next_action


        ##########################
        # running GBFS from updated world
        p = SpaceshipProblem(self.my_world)
        result = check_problem(p, (lambda p: best_first_graph_search(p, p.h)), self.timeout)
        ##########################

        self.gbfs_route = result[2]

        if not self.gbfs_route:
            if not spaceships or not devices:
                if STEPS < self.nb_steps:
                    next_action = ("reset",)
                    self.my_world = (self.original_world[0], self.original_world[1], self.original_world[2])
                    self.gbfs_route = self.original_gbfs
                    self.last_action = ()
                    return (next_action)

            else:
                next_action = ("turn_on", devices[0][0], devices[0][1])
                self.last_action = next_action
                return next_action

        else:
            next_action = self.gbfs_route[0]
            self.last_action = next_action
            del self.gbfs_route[0]
            self.update_my_world(next_action)
            return next_action


    def update_my_world(self, action):
        # action is one of the actions as in part 1
        spaceships = self.my_world[0]  # tuple of: (ShipName, Location)
        devices = self.my_world[1]  # tuple of: (ShipName, DeviceName, Power, Calibrated, CalibrationTarget,FinalTarget, Hit)
        all_targets = self.my_world[2]

        if action[0] == "move":
            # act = ("move", ship_name, location, move_to)
            stemplist = [list(x) for x in spaceships]
            for ship in stemplist:
                if ship[0] == action[1]:
                    if ship[1] == action[2]:
                        ship[1] = action[3]
            spaceships = tuple([tuple(x) for x in stemplist])
        elif action[0] == "turn_on":
            # act = ("turn_on", ship_name, device_name)
            # devices is a tuple of: (ShipName, DeviceName, Power, Calibrated, CalibrationTarget, FinalTarget,Hit)
            dtemplist = [list(x) for x in devices]
            for device in dtemplist:
                if device[0] == action[1] and device[1] == action[2]:
                    device[2] = 1
                elif device[0] == action[1] and device[1] != action[2]:
                    device[2] = 0
                    device[3] = 0
            devices = tuple([tuple(x) for x in dtemplist])


        elif action[0] == "calibrate":
            # act = ("calibrate", ship_name, device_name, cali_target)
            dtemplist = [list(x) for x in devices]
            for device in dtemplist:
                if device[0] == action[1] and device[1] == action[2]:
                    device[3] = 1
            devices = tuple([tuple(x) for x in dtemplist])

        elif action[0] == "use":
            # act = ("use", ship_name, device_name, hit_target)
            dtemplist = [list(x) for x in devices]
            for device in dtemplist:
                if device[0] == action[1] and device[1] == action[2] and device[5] == action[3]:
                    device[6] = 1
            devices = tuple([tuple(x) for x in dtemplist])

        self.my_world = (spaceships, devices, all_targets)





###################################################
##from ex1.py from part1
class SpaceshipProblem(Problem):
    """This class implements a spaceship problem"""

    def __init__(self, initial):
        """Don't forget to set the goal or implement the goal test
        You should change the initial to your own representation"""
        Problem.__init__(self, initial)

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
        global lasers_locations
        global edge_locations
        global GRID_LIMIT
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
        for ship_name, ship_location in ships:
            if ship_location in lasers_locations:
                c += 0.8
            if ship_location in edge_locations:
                c += 0.3
        return (c)
######################################################
#from check.py from part1
def timeout_exec(func, args=(), kwargs={}, timeout_duration=10, default=None):
    """This function will spawn a thread and run the given function
    using the args, kwargs and return the given default value if the
    timeout_duration is exceeded.
    """
    import threading
    class InterruptableThread(threading.Thread):
        def __init__(self):
            threading.Thread.__init__(self)
            self.result = default

        def run(self):
            try:
                self.result = func(*args, **kwargs)
            except Exception as e:
                self.result = (-3, -3, e)

    it = InterruptableThread()
    it.start()
    it.join(timeout_duration)
    if it.isAlive():
        return default
    else:
        return it.result

def check_problem(p, search_method, timeout):
    """ Constructs a problem using ex1.create_poisonserver_problem,
    and solves it using the given search_method with the given timeout.
    Returns a tuple of (solution length, solution time, solution)
    (-2, -2, None) means there was a timeout
    (-3, -3, ERR) means there was some error ERR during search"""

    t1 = time.time()
    s = timeout_exec(search_method, args=[p], timeout_duration=timeout)
    t2 = time.time()

    if isinstance(s, Node):
        solve = s
        solution = list(map(lambda n: n.action, solve.path()))[1:]
        return (len(solution), t2 - t1, solution)
    elif s is None:
        return (-2, -2, None)
    else:
        return s