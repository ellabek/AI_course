__author__ = 'Ella'


import time
import logic
import search
import copy
import itertools
import random

GRID_LIMIT = 0
my_world = ()

class SpaceshipController:
    "This class is a controller for a spaceship problem."
    def __init__(self, problem, num_of_transmitters):
    #building representation for world as in part 1
    # problem is a tuple of all the input

        global GRID_LIMIT
        global my_world
        GRID_LIMIT = problem[0]

        spaceships = ()  # tuple of: (ShipName, Location)
        devices = ()  # tuple of: (ShipName, DeviceName, Power, Calibrated, CalibrationTarget, FinalTarget,Hit)
        all_targets = ()

        #define class propKB to use later
        self.lasers_logic = logic.PropKB()
        #define dictionary to save all grid to use later
        self.grid_dict = {}
        for x in range(GRID_LIMIT):
            for y in range(GRID_LIMIT):
                for z in range(GRID_LIMIT):
                    self.grid_dict[(x, y, z)] = logic.expr('L' + str(x) + str(y) + str(z))

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
        my_world = (spaceships, devices, all_targets)

    def minus_key(self, key, dictionary):
        shallow_copy = dict(dictionary)
        del shallow_copy[key]
        return shallow_copy

    def get_neighbors(self, location):
        global GRID_LIMIT
        neighbors = ()
        if (location[0] + 1 < GRID_LIMIT):
            # x move up
            # x coordinate within grid
            n = (location[0] + 1, location[1], location[2])
            neighbors = (n,) + neighbors
        if (location[0] - 1 >= 0):
            # x move down
            n = (location[0] - 1, location[1], location[2])
            neighbors = (n,) + neighbors

        if (location[1] + 1 < GRID_LIMIT):
            # y move up
            # y coordinate within grid
            n = (location[0], location[1] + 1, location[2])
            neighbors = (n,) + neighbors
        if (location[1] - 1 >= 0):
            # y move down
            n = (location[0], location[1] - 1, location[2])
            neighbors = (n,) + neighbors

        if (location[2] + 1 < GRID_LIMIT):
            # z move up
            # z coordinate within grid
            n = (location[0], location[1], location[2] + 1)
            neighbors = (n,) + neighbors
        if (location[2] - 1 >= 0):
            # z move down
            n = (location[0], location[1], location[2] - 1)
            neighbors = (n,) + neighbors
        return neighbors

    def get_next_action(self, observation):
        # get observation for the current state and return next action to apply (and None if no action is applicable)
        #observation is a dictionary with spaceship_name:number_of_laser_around it.

        global my_world
        print("my_world_is:")
        print(my_world)

        print("this is the observation:")
        print (observation)

        spaceships = my_world[0]
        devices = my_world[1]
        all_targets = my_world[2]

        #update spaceships and devices if there is spaceship that exploded
        for device in devices:
            if device[0] in observation:
                ship_name = device[0]
                if observation[ship_name] == -1: #ship exploded
                    temp_list = list(devices)
                    temp_list.remove(device)
                    devices = tuple(temp_list)
        for ship in spaceships:
            if ship[0] in observation:
                ship_name = ship[0]
                if observation[ship_name] == -1:  # ship exploded
                    temp_list = list(spaceships)
                    temp_list.remove(ship)
                    spaceships = tuple(temp_list)
        #updated world after removing ships that exploded. important for the GBFS running in the next lines
        my_world = (spaceships, devices, all_targets)

        #all ships exploded
        if not devices or not spaceships:
            return None

        ##########################
        #running GBFS from current world
        p = SpaceshipProblem(my_world)
        timeout = 60
        result = check_problem(p, (lambda p: search.best_first_graph_search(p, p.h)), timeout)
        print("GBFS ", result)
        ##########################

        #updating the world representation
        next_action = result[2][0]

        if next_action[0] in ("turn_on", "use", "calibrate"):
            self.update_my_world(next_action)
            return next_action

        #for all locations without lasers, make a tuple of their neighbors and mark them as safe - without lasers.
        all_neighbors = ()
        all_neighbors = (next_action[2],) + all_neighbors
        for sname, nb_lasers in observation.items():
            if nb_lasers == 0:
                for shipname, location in spaceships:
                    if shipname == sname:
                        ship_all_neighbors = self.get_neighbors(location)
                        for i in ship_all_neighbors:
                            if i not in all_neighbors:
                                all_neighbors = (i,) + all_neighbors
        for i in all_neighbors:
            self.lasers_logic.tell(~(self.grid_dict[i]))

        #if the action is move for some ship and there isn't lasers around it, go ahead and do it.
        for sname, nb_lasers in observation.items():
            if next_action[1] == sname and nb_lasers == 0 and next_action[0] == "move":
                self.update_my_world(next_action)
                return next_action

        #if the code is here, then the gbfs wants to move a ship with lasers around it
        #next_action[0] = "move", next_action[1] = ship name, next_action[2] = from, next_action[3] = to
        n_combinations = []
        for ship_name, ship_location in spaceships:
            if ship_name == next_action[1]:
                near_by_n = self.get_neighbors(ship_location)
                near_by_n = (ship_location,) + near_by_n
                nb_lasers = observation[ship_name]
                n_combinations = (itertools.combinations(list(near_by_n), len(near_by_n) - nb_lasers))
        combination_list = list(n_combinations)
        small_combinations = (combination_list[0], combination_list[1], combination_list[2])
        logic_list = []
        for combination in small_combinations:
            temp = []
            for coord in combination:
                temp.append(~self.grid_dict[coord])
            logic_list.append(logic.associate('&', temp))

        self.lasers_logic.tell(logic.associate('|', logic_list))
        logic_answer = logic.dpll_satisfiable(logic.to_cnf(logic.associate('&', self.lasers_logic.clauses)))
        #logic answer contains a dict of Lxyz = Flase/True. when False means that the (x,y,z) location is safe, and unsafe
        #(contains lasers) otherwise
        #if "to_location" of GBFS is in logic_answer and is false - use it,
        #else we would like to choose a random one that is not our current location

        print ("logic answer:" ,logic_answer)
        # gbfs_to_location = self.grid_dict[next_action[3]]

        # logic_answer.delete(self.grid_dict[next_action[2]])
        for k, v in logic_answer.items():
            if v == True:
                logic_answer = self.minus_key(k, logic_answer)
        #remove from logic answer not neighbors
        nears = ()
        neighbors = self.get_neighbors(next_action[2])
        for n in neighbors:
            temp = self.grid_dict[n]
            nears = (temp,) + nears
        for l in logic_answer:
            if l not in nears:
                logic_answer = self.minus_key(l, logic_answer)
        #remove targets locations
        for t in all_targets:
            temp = self.grid_dict[t]
            if temp in logic_answer:
                logic_answer = self.minus_key(temp,logic_answer)
        #remove spaceships locations
        for ship_name, location in spaceships:
            temp = self.grid_dict[location]
            if temp in logic_answer:
                logic_answer = self.minus_key(temp, logic_answer)


        print("whats left for random: ",list(logic_answer.keys()))
        random_to_location = random.choice(list(logic_answer.keys()))
        print("random choise:", random_to_location)
        if not random_to_location: #empty
            return None
        #return Lxyz form to (x,y,z)
        new_to_location = ()
        for k , v in self.grid_dict.items():
            if v == random_to_location:
                new_to_location = k
        print("new_to_location:", new_to_location)
        new_next_action = ("move", next_action[1], next_action[2],new_to_location)
        print("new next location", new_next_action)
        self.update_my_world(new_next_action)
        return new_next_action




    def update_my_world(self,action):
        #action is one of the actions as in part 1
        global my_world
        spaceships = my_world[0]  # tuple of: (ShipName, Location)
        devices = my_world[1]  # tuple of: (ShipName, DeviceName, Power, Calibrated, CalibrationTarget,FinalTarget, Hit)
        all_targets = my_world[2]

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

        my_world = (spaceships, devices, all_targets)

###################################################
##from ex1.py from part1
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

    if isinstance(s, search.Node):
        solve = s
        solution = list(map(lambda n: n.action, solve.path()))[1:]
        return (len(solution), t2 - t1, solution)
    elif s is None:
        return (-2, -2, None)
    else:
        return s
#######################################################################3
