"""
Functions for changing and reading the navigation state of a surrendered ship.
Some miscellaneous stuff related to surrendered ships' navigation is here too.
"""

from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.query import to_space_object
from sbs_utils.procedural.timers import is_timer_set, set_timer, is_timer_finished #, clear_timer
from sbs_utils.procedural.execution import task_schedule, task_cancel
from sbs_utils.procedural.space_objects import target_pos

from data.missions.common.distance_utils import broad_test_around_position, is_distance_closer_than_or_equal_to

# ----- Gameplay constants -----
# Change these to tweak gameplay balance

# durations
def seconds_before_run_away_min():
    return 60
def seconds_before_deletion_min():
    return 120

def seconds_between_can_delete_checks():
    return 30
def seconds_between_run_away_checks_when_stopped():
    return 10
def seconds_between_close_enough_to_location_and_run_away_checks():
    return 10
def seconds_between_update_followed_ship_position_and_run_away_checks():
    return 5

# distances
def compliance_radius():
    return 10000

def close_enough_to_have_arrived_radius():
    return 150

def close_enough_to_spawnpoint_for_deletion_radius():
    return 1000

def player_prevents_deletion_taxicab_distance():
    return 16000

# ----- initializing -----

def initialize_nav_state(surrendered_ship_object):
    """
    Initializes the navigation state for a surrendered ship.
    Called when the ship surrenders.
    """
    _set_nav_state(surrendered_ship_object.id, None, nav_state_to_spawnpoint_no_deletion(), expect_nav_task_already_running=False)
    _navigate_to(surrendered_ship_object.id, surrendered_ship_object.spawn_pos, throttle=1.5)

# ----- player commands to surrendered ships (public) -----

def command_go_on_your_way(surrendered_ship_id, commanded_by_ship_id):
    """
    A player ship attempts to command a surrendered ship to go on their way.
    If the surrendered ship is destroyed, fails.
    Otherwise, succeeds (since it isn't really a command, more like a lack of one).
    Args:
        surrendered_ship_id (int): id of the surrendered ship
        commanded_by_ship_id (int): id of the player ship
    Returns:
        True if succeeded, False if failed
    """
    surrendered_ship_object = to_space_object(surrendered_ship_id)
    if surrendered_ship_object is None:
        return False
    # Reset the timer since last successful nav command,
    # only if the commanding ship is close enough.
    elif is_within_compliance_radius(surrendered_ship_id, commanded_by_ship_id):
        set_timer(surrendered_ship_id, timer_key_distant_commands_grace_period(commanded_by_ship_id), seconds=seconds_before_run_away_min())
    
    prev_nav_state = get_nav_state(surrendered_ship_id)
    if prev_nav_state == nav_state_to_spawnpoint_no_deletion() or prev_nav_state == nav_state_to_spawnpoint_deletion_ok():
        # keep current state
        return True
    elif prev_nav_state == nav_state_running_away_no_deletion():
        _set_nav_state(surrendered_ship_id, commanded_by_ship_id, nav_state_to_spawnpoint_no_deletion())
    elif prev_nav_state == nav_state_running_away_deletion_ok():
        _set_nav_state(surrendered_ship_id, commanded_by_ship_id, nav_state_to_spawnpoint_deletion_ok())
    else: # stopped / going to location / following ship
        _set_nav_state(surrendered_ship_id, commanded_by_ship_id, nav_state_to_spawnpoint_no_deletion())
    
    _navigate_to(surrendered_ship_id, surrendered_ship_object.spawn_pos, throttle=1.5)
    return True

def command_stop(surrendered_ship_id, commanded_by_ship_id):
    """
    A player ship attempts to command a surrendered ship to stop where they are.
    If the surrendered ship is destroyed, fails.
    If the surrendered ship is not compliant, fails.
    Otherwise, succeeds.
    Args:
        surrendered_ship_id (int): id of the surrendered ship
        commanded_by_ship_id (int): id of the player ship
    Returns:
        True if succeeded, False if failed
    """
    surrendered_ship_object = to_space_object(surrendered_ship_id)
    if surrendered_ship_object is None:
        return False
    if not _try_nav_demand(surrendered_ship_id, commanded_by_ship_id):
        _transition_to_running_away_if_going_to_spawnpoint(surrendered_ship_id, commanded_by_ship_id)
        return False
    nav_stop(surrendered_ship_object, commanded_by_ship_id)
    return True

def nav_stop(surrendered_ship_object, commanded_by_ship_id):
    """
    Makes a surrendered ship stop where it is.
    Args:
        surrendered_ship_id (int): id of the surrendered ship
        commanded_by_ship_id (int | None): id of the player ship, or None if no
            particular player ship is giving the command (this means the ship
            will never run away, i.e. keep doing this command until told otherwise)
    """
    _set_nav_state(surrendered_ship_object.id, commanded_by_ship_id, nav_state_commanded_to_stop())
    _navigate_to(surrendered_ship_object.id, surrendered_ship_object.pos, throttle=0)

def command_to_location(surrendered_ship_id, commanded_by_ship_id, position):
    """
    A player ship attempts to command a surrendered ship to go to a specific location.
    If the surrendered ship is not compliant, fails.
    Otherwise, succeeds.
    Args:
        surrendered_ship_id (int): id of the surrendered ship
        commanded_by_ship_id (int): id of the player ship
        position (Vec3): position the surrendered ship is being commanded to go to
    Returns:
        True if succeeded, False if failed
    """
    if not _try_nav_demand(surrendered_ship_id, commanded_by_ship_id):
        _transition_to_running_away_if_going_to_spawnpoint(surrendered_ship_id, commanded_by_ship_id)
        return False
    nav_to_location(surrendered_ship_id, commanded_by_ship_id, position)
    return True

def nav_to_location(surrendered_ship_id, commanded_by_ship_id, position):
    """
    Makes a surrendered ship navigate to a location.
    Args:
        surrendered_ship_id (int): id of the surrendered ship
        commanded_by_ship_id (int | None): id of the player ship, or None if no
            particular player ship is giving the command (this means the ship
            will never run away, i.e. keep doing this command until told otherwise)
        position (Vec3): position the surrendered ship is being commanded to go to
    """
    _set_nav_state(surrendered_ship_id, commanded_by_ship_id, nav_state_commanded_to_location())
    set_inventory_value(surrendered_ship_id, inventory_key_to_location_xyz(), position)
    _navigate_to(surrendered_ship_id, position)

def command_follow_ship(surrendered_ship_id, commanded_by_ship_id, target_ship_id):
    """
    A player ship attempts to command a surrendered ship to follow a specific ship.
    If the surrendered ship is destroyed, fails.
    If the surrendered ship is not compliant, fails.
    Otherwise, succeeds.
    Args:
        surrendered_ship_id (int): id of the surrendered ship
        commanded_by_ship_id (int): id of the player ship
        position (Vec3): position the surrendered ship is being commanded to go to
    Returns:
        True if succeeded, False if failed
    """
    target_ship_object = to_space_object(target_ship_id)
    if target_ship_object is None:
        return False
    if not _try_nav_demand(surrendered_ship_id, commanded_by_ship_id):
        _transition_to_running_away_if_going_to_spawnpoint(surrendered_ship_id, commanded_by_ship_id)
        return False
    nav_follow_ship(surrendered_ship_id, commanded_by_ship_id, target_ship_object)
    return True

def nav_follow_ship(surrendered_ship_id, commanded_by_ship_id, target_ship_object):
    """
    Makes a surrendered ship follow another ship.
    Args:
        surrendered_ship_id (int): id of the surrendered ship
        commanded_by_ship_id (int | None): id of the player ship, or None if no
            particular player ship is giving the command (this means the ship
            will never run away, i.e. keep doing this command until told otherwise)
        target_ship_object (space object): the ship that the surrendered ship is being
            commanded to follow to
    """
    _set_nav_state(surrendered_ship_id, commanded_by_ship_id, nav_state_commanded_to_follow_ship())
    set_inventory_value(surrendered_ship_id, inventory_key_follow_ship_id(), target_ship_object.id)
    _navigate_to(surrendered_ship_id, target_ship_object.pos)

# ----- private setters -----

def _try_nav_demand(surrendered_ship_id, commanded_by_ship_id):
    """
    A player ship attempts to command a surrendered ship to do something.
    If the surrendered ship is not compliant, fails.
    Otherwise, succeeds.
    'Abstract' method; this is meant to be called by other functions for giving specific types of commands.
    Args:
        surrendered_ship_id (int): id of the surrendered ship
        commanded_by_ship_id (int): id of the player ship
    Returns:
        True if succeeded, False if failed
    """
    is_successful, is_close_by = is_compliant(surrendered_ship_id, commanded_by_ship_id)
    if is_close_by:
        set_timer(surrendered_ship_id, timer_key_distant_commands_grace_period(commanded_by_ship_id), seconds=seconds_before_run_away_min())
    return is_successful

def _transition_to_running_away_if_going_to_spawnpoint(surrendered_ship_id, commanded_by_ship_id):
    """
    If the surrendered ship was going on its way to its spawnpoint, then changes
    its navigation state to running away variant (without changing whether it's
    ok for the ship to be deleted).
    """
    if get_nav_state(surrendered_ship_id) == nav_state_to_spawnpoint_no_deletion():
        _set_nav_state(surrendered_ship_id, commanded_by_ship_id, nav_state_running_away_no_deletion())
    elif get_nav_state(surrendered_ship_id) == nav_state_to_spawnpoint_deletion_ok():
        _set_nav_state(surrendered_ship_id, commanded_by_ship_id, nav_state_running_away_deletion_ok())

def _try_run_away(surrendered_ship_id, commanded_by_ship_id, skip_task_cancel=False):
    """
    A surrendered ship attempts to run away from a player ship; i.e. defy their
    commands and quietly slip away to their spawnpoint.
    If the surrendered ship is destroyed, fails.
    If surrendered ship's last command was not given by any particular player ship, fails.
    If the surrendered ship is compliant (see is_compliant), fails.
    Otherwise, succeeds (i.e. the ship runs away).
    Args:
        surrendered_ship_id (int): id of the surrendered ship
        commanded_by_ship_id (int | None): id of the player ship, or None if its
            last command was not given by any particular player ship.
        skip_task_cancel (bool | None): Default False. Set to True to skip
            cancelling the surrendered ship's currently running navigation task.
            This is necessary when calling this function from the navigation task
            itself.
            When skip_task_cancel is set to True and this function succeeds, then
            the currently-running navigation task must be ended in some other way
            before the script yields control to the engine (so no awaits or jumps),
            in order to ensure the surrendered ship has exactly one navigation task
            running at all times.
    Returns:
        True if the surrendered ship runs away, False if they continue complying
    """
    surrendered_ship_object = to_space_object(surrendered_ship_id)
    if surrendered_ship_object is None:
        return False
    elif commanded_by_ship_id is None:
        return False
    elif is_compliant(surrendered_ship_id, commanded_by_ship_id)[0]:
        return False
    _set_nav_state(surrendered_ship_id, commanded_by_ship_id, nav_state_running_away_no_deletion(), skip_task_cancel=skip_task_cancel)
    # TODO: be smarter about routing; prioritize not getting close to the
    # player ship that just commanded it or any other player ships
    _navigate_to(surrendered_ship_id, surrendered_ship_object.spawn_pos, throttle=1.5)
    return True

def _set_nav_state(surrendered_ship_id, commanded_by_ship_id, nav_state, expect_nav_task_already_running=True, skip_task_cancel=False):
    """
    Changes the navigation state of a surrendered ship.
    If the surrendered ship is destroyed, nothing happens.
    Args:
        surrendered_ship_id (int): id of the surrendered ship
        commanded_by_ship_id (int): id of the player ship
        nav_state (quasi-enum): new navigation state for the surrendered ship.
            Must be a value returned from one of the following functions
            (This is essentially an enum that's mast-compatible)
            nav_state_to_spawnpoint_no_deletion()
            nav_state_running_away_no_deletion()
            nav_state_to_spawnpoint_deletion_ok()
            nav_state_running_away_deletion_ok()
            nav_state_commanded_to_stop()
            nav_state_commanded_to_location()
            nav_state_commanded_to_follow_ship()
        expect_nav_task_already_running (bool | None): Default True. Set to False if
            the surrendered ship shouldn't have a currently running navigation task,
            such as when a ship surrenders and its navigation state is being set
            for the first time. Currently, this doesn't have any functional impact,
            but it's useful for assertions or logging errors in case there's a task
            running but there shouldn't be or vice versa.
        skip_task_cancel (bool | None): Default False. Set to True to skip
            cancelling the surrendered ship's currently running navigation task.
            This is necessary when calling this function from the navigation task
            itself.
            When skip_task_cancel is set to True, then the currently-running
            navigation task must be ended in some other way before the script yields
            control to the engine (so no awaits or jumps), in order to ensure the
            surrendered ship has exactly one navigation task running at all times.
    """
    surrendered_ship_object = to_space_object(surrendered_ship_id)
    if surrendered_ship_object is None:
        return
    set_inventory_value(surrendered_ship_id, inventory_key_nav_state(), nav_state)
    set_inventory_value(surrendered_ship_id, inventory_key_to_location_xyz(), None)
    set_inventory_value(surrendered_ship_id, inventory_key_follow_ship_id(), None)
    
    old_nav_task = get_inventory_value(surrendered_ship_id, inventory_key_surrendered_nav_task())
    new_nav_task = task_schedule(nav_state, data={"SURRENDERED_SHIP_ID": surrendered_ship_id, "COMMANDED_BY_SHIP_ID": commanded_by_ship_id})
    set_inventory_value(surrendered_ship_id, inventory_key_surrendered_nav_task(), new_nav_task)
    
    if old_nav_task is not None:
        # old_nav_task might be the one calling this function; if so, don't cancel it
        if not skip_task_cancel:
            task_cancel(old_nav_task)

def _navigate_to(surrendered_ship_id, position, throttle=1):
    """
    Makes a surrendered ship move to a specific position.
    If the surrendered ship is destroyed, nothing happens.
    Args:
        surrendered_ship_id (int): id of the surrendered ship
        position (Vec3): position for the surrendered ship to go to
        throttle (float | None): Default 1. How fast the surrendered ship will move
            towards the given position.
    """
    surrendered_ship_object = to_space_object(surrendered_ship_id)
    if surrendered_ship_object is None:
        return
    # Setting target_id (to a nontrivial, real id) will cause
    # the surrendered ship to attack whatever ship target_id is
    target_pos(surrendered_ship_id, position.x, position.y, position.z, throttle=throttle, target_id=0)

# ----- getters (public) -----

def get_nav_state(surrendered_ship_id):
    """
    Returns the surrendered ship's state of navigation,
    in the form of a value returned from one of the following functions
    (This is essentially an enum that's mast-compatible)
    nav_state_to_spawnpoint_no_deletion()
    nav_state_running_away_no_deletion()
    nav_state_to_spawnpoint_deletion_ok()
    nav_state_running_away_deletion_ok()
    nav_state_commanded_to_stop()
    nav_state_commanded_to_location()
    nav_state_commanded_to_follow_ship()
    """
    return get_inventory_value(surrendered_ship_id, inventory_key_nav_state())

def is_in_commanded_nav_state(surrendered_ship_id):
    """
    Returns True if the given surrendered ship is doing something that a player
    ship commanded it to do.
    Otherwise, returns False.
    """
    return is_nav_state_commanded(get_nav_state(surrendered_ship_id))

def is_nav_state_commanded(nav_state):
    """
    Returns True if the given navigation state is something that a player ship 
    commanded.
    Otherwise, returns False.
    """
    return nav_state in { nav_state_commanded_to_stop(), nav_state_commanded_to_location(), nav_state_commanded_to_follow_ship() }

def is_within_compliance_radius(surrendered_ship_id, commanded_by_ship_id):
    """
    Returns True if the given player ship is close enough to the given surrendered
    ship to ensure the surrendered ship will comply with the player ship's commands.
    (The exact compliance radius is determined by compliance_radius().)
    Otherwise, returns False.
    If the surrendered ship is destroyed, returns False.
    """
    if surrendered_ship_id is None or commanded_by_ship_id is None:
        return False
    surrendered_ship_object = to_space_object(surrendered_ship_id)
    if surrendered_ship_object is None:
        return False
    commanded_by_ship_object = to_space_object(commanded_by_ship_id)
    if commanded_by_ship_object is None:
        return False
    return is_distance_closer_than_or_equal_to(surrendered_ship_object.pos, commanded_by_ship_object.pos, compliance_radius())

def is_compliant(surrendered_ship_id, commanded_by_ship_id):
    """
    Whether the given surrendered ship will comply with navigation commands from
    the given player ship.
    Args:
        surrendered_ship_id (int): id of the surrendered ship
        commanded_by_ship_id (int): id of the player ship
    Returns:
        (bool, bool): True if the surrendered ship is compliant, otherwise False;
            True if the player ship and surrendered ship are within the compliance radius.
            These two return values can differ in the case of a player ship having
            recently left the radius of compliance, before the grace period expires.
    """
    if get_inventory_value(surrendered_ship_id, "secret_codecase_surrender"):
        # currently it doesn't matter what the second return value here is
        # but calculate and return it anyway for robustness against future changes
        return True, is_within_compliance_radius(surrendered_ship_id, commanded_by_ship_id)
    elif is_within_compliance_radius(surrendered_ship_id, commanded_by_ship_id):
        return True, True
    elif not is_timer_set(surrendered_ship_id, timer_key_distant_commands_grace_period(commanded_by_ship_id)):
        return False, False
    else:
        is_grace_period_timer_running = not is_timer_finished(surrendered_ship_id, timer_key_distant_commands_grace_period(commanded_by_ship_id))
        return is_grace_period_timer_running, False

def get_commanded_location(surrendered_ship_id):
    """
    If the surrendered ship is currently navigating to a specific location because
    it was commanded to by a player ship, returns that location (Vec3).
    Otherwise, returns None.
    """
    if get_nav_state(surrendered_ship_id) == nav_state_commanded_to_location():
        return get_inventory_value(surrendered_ship_id, inventory_key_to_location_xyz())
    else:
        return None

def get_commanded_follow_ship_id(surrendered_ship_id):
    """
    If the surrendered ship is currently following a ship because it was commanded
    to by a player ship, returns that ship's id (int).
    Otherwise, returns None.
    """
    if get_nav_state(surrendered_ship_id) == nav_state_commanded_to_follow_ship():
        return get_inventory_value(surrendered_ship_id, inventory_key_follow_ship_id())
    else:
        return None

def is_close_enough_to_commanded_location(surrendered_ship_id):
    """
    Returns True if the surrendered ship is close enough to the location that it
    was commanded to go to that it can be considered as having arrived.
    Otherwise, returns False.
    If the surrendered ship is destroyed, returns False.
    """
    surrendered_ship_object = to_space_object(surrendered_ship_id)
    if surrendered_ship_object is None:
        return False
    return is_distance_closer_than_or_equal_to(surrendered_ship_object.pos, get_commanded_location(surrendered_ship_id), close_enough_to_have_arrived_radius())

def is_close_enough_to_spawnpoint_for_deletion(surrendered_ship_id):
    """
    Returns True if the surrendered ship is close enough to its spawnpoint that
    it might be able to be deleted.
    Otherwise, returns False.
    If the surrendered ship is destroyed, returns False.
    """
    surrendered_ship_object = to_space_object(surrendered_ship_id)
    if surrendered_ship_object is None:
        return False
    return is_distance_closer_than_or_equal_to(surrendered_ship_object.pos, surrendered_ship_object.spawn_pos, close_enough_to_spawnpoint_for_deletion_radius())

def is_a_player_too_close_for_deletion(surrendered_ship_id):
    """
    Returns True if there is at least one player ship that's close enough to
    the given surrendered ship such that the surrendered ship shouldn't be deleted.
    Otherwise, returns False.
    If the surrendered ship is destroyed, returns False.
    """
    surrendered_ship_object = to_space_object(surrendered_ship_id)
    if surrendered_ship_object is None:
        return False
    # 0x20 is bitmask value to filter for player ships.
    # This will include the ship used for the gamemaster console.
    # I don't know whether this filter will include single-seat craft or not:
    # https://github.com/orgs/artemis-sbs/discussions/524
    # I don't think it matters very much whether either of those being nearby
    # prevents surrendered ships from being deleted though.
    nearby_player_ships = broad_test_around_position(surrendered_ship_object.pos, player_prevents_deletion_taxicab_distance() * 2, player_prevents_deletion_taxicab_distance() * 2, 0x20)
    return len(nearby_player_ships) > 0

# ----- Technical Constants -----
# Changing these won't impact gameplay

# nav states - these need to match the names of labels in surrendered_navigation.mast
def nav_state_to_spawnpoint_no_deletion():
    return "surr_nav_state_to_spawnpoint_no_deletion"
def nav_state_running_away_no_deletion():
    return "surr_nav_state_running_away_no_deletion"
def nav_state_to_spawnpoint_deletion_ok():
    return "surr_nav_state_to_spawnpoint_deletion_ok"
def nav_state_running_away_deletion_ok():
    return "surr_nav_state_running_away_deletion_ok"
def nav_state_commanded_to_stop():
    return "surr_nav_state_commanded_to_stop"
def nav_state_commanded_to_location():
    return "surr_nav_state_commanded_to_location"
def nav_state_commanded_to_follow_ship():
    return "surr_nav_state_commanded_to_follow_ship"

# inventory keys
def inventory_key_nav_state():
    return "srnvst"

def inventory_key_surrendered_nav_task():
    return "srnv_task"

def inventory_key_to_location_xyz():
    return "srnv_to_xyz"
def inventory_key_follow_ship_id():
    return "srnv_follow_ship"

# timer keys
def timer_key_distant_commands_grace_period(commanded_by_ship_id):
    return f"srnv_distant_grace_{commanded_by_ship_id}"

def timer_key_no_deletion_grace_period():
    return "srnv_del_grace"
