from enum import Enum
from random import random, randrange

from sbs_utils.procedural.comms import comms_navigate, comms_receive, comms_receive_internal
from sbs_utils.procedural.execution import get_shared_variable, set_shared_variable, set_variable
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.roles import add_role, has_role, remove_role
from sbs_utils.procedural.signal import signal_emit

from data.missions.common.distance_utils import is_distance_farther_than_or_equal_to
from data.missions.common.pirate_features_definitions import is_raider
# Can't import this because 'fleets' comes after 'comms' alphabetically
# See the bottom of this file for the workaround
#from data.missions.legendarymissions.fleets.map_common import fleet_remove_ship

# ----- Gameplay Constants -----

# Consider tweaking these to affect gameplay balance

_RADIUS_CLOSE_ENOUGH_FOR_SURRENDER = 5000
_RADIUS_CLOSE_ENOUGH_FOR_CODE_CASE = _RADIUS_CLOSE_ENOUGH_FOR_SURRENDER

# _CHANCE_BRAVE + _CHANCE_COWARDLY must be less than or equal to 1.0
_CHANCE_BRAVE = 0.15
_CHANCE_COWARDLY = 0.15

# Absolute range across all possible ships
_BASE_SHIELD_THRESHOLD_FOR_SURRENDER_MIN = 10 # Inclusive
_BASE_SHIELD_THRESHOLD_FOR_SURRENDER_MAX = 50 # Exclusive

def _get_base_shield_threshold_for_surrender_range(ship_id):
    """
    Range of possible shield thresholds under which this ship will surrender.
    Higher numbers means the ship will surrender more easily, and
    lower numbers means the ship will surrender with more difficulty.
    See setup_surrender_conditions() and/or test_surrenderable() for more exact
    details of how the base shield thresholds are used.
    Valid range is 0 to 100. Minimum is inclusive, and maximum is exclusive.
    """
    if is_brave(ship_id):
        return _BASE_SHIELD_THRESHOLD_FOR_SURRENDER_MIN, 30
    elif is_cowardly(ship_id):
        return 30, _BASE_SHIELD_THRESHOLD_FOR_SURRENDER_MAX
    else:
        return _BASE_SHIELD_THRESHOLD_FOR_SURRENDER_MIN, _BASE_SHIELD_THRESHOLD_FOR_SURRENDER_MAX

def _get_chance_never_surrender(ship_id):
    """
    Float between 0 and 1 representing the chance that this ship will never surrender
    0.0 means the ship will always be surrenderable
    1.0 means the ship will never be surrenderable
    0.5 means there's a 50%-50% chance of being surrenderable
    """
    if is_brave(ship_id):
        return 0.4
    elif is_cowardly(ship_id):
        return 0.0
    else:
        return 0.2

# ----- Which enemy npcs can be asked to surrender? -----

def can_be_asked_to_surrender(ship_id):
    """
    Returns True if this ship should be able to be asked by players to surrender.
    Otherwise, returns False.
    
    Currently, only enemy ships can be asked to surrender; not bases or single-seat craft.
    (More precisely, this is any object with the 'ship' and 'raider' roles.)
    
    It doesn't matter if the ship would ever react or already has reacted to a
    surrender request with a 'never' response; this function should return True
    for these never-surrender ships.
    
    If the ship has already surrendered, then this function should return False.
    """
    # Note that is_enemy excludes surrendered ships, b/c the raider role
    # gets removed when a ship surrenders
    # If that ever changes, then also check 'not has_surrendered(ship_id)'
    return has_role(ship_id, "ship") and is_raider(ship_id)

def is_surrendering_comms_allowed(COMMS_ORIGIN_ID, COMMS_SELECTED_ID):
    """
    Returns True if the comms buttons for surrendering ships should be enabled
    between the origin and selected ships, otherwise False
    """
    return has_role(COMMS_ORIGIN_ID, "__player__") and can_be_asked_to_surrender(COMMS_SELECTED_ID)

# ----- Enemy npc surrendered state -----

def has_surrendered(ship_id):
    """ Returns True if the ship has surrendered, otherwise False """
    return has_role(ship_id, _ROLE_KEY_SURRENDERED)

def _set_surrendered(ship_object, player_ship_object, via_code_case=False):
    """
    Call this to indicate the ship has surrendered.
    Does not consume the code case, if one was used.
    """
    
    add_role(ship_object.id, _ROLE_KEY_SURRENDERED)
    ship_object.data_set.set("surrender_flag", 1)
    
    if via_code_case:
        set_inventory_value(ship_object.id, _INVENTORY_KEY_IS_CODE_CASE_SURRENDER, True)
    
    # Emit this prior to removing the raider role, so that listeners can
    # distinguish raiders surrendering from other vessels surrendering.
    # (The latter does not exist in the game currently, but might in the future.)
    signal_emit("npc_surrendered", data={"SURRENDERED_SHIP_ID": ship_object.id, "REQUESTED_BY_PLAYER_SHIP_ID": player_ship_object.id, "IS_VIA_CODE_CASE": via_code_case})
    
    remove_role(ship_object.id, "raider")
    fleet_remove_ship(ship_object.id)
    
    GAME_STATISTICS = get_game_statistics()
    GAME_STATISTICS.record_vessel_surrendered(COMMS_SELECTED)

# ----- Enemy npc conditions for surrendering -----

def setup_surrender_conditions(ship_id):
    """
    Randomly determines whether this ship will ever surrender if asked,
    and if so under what conditions it will surrender.
    This should be called as soon as the ship is spawned.
    
    Each enemy ship that can be surrendered gets assigned a random
    base shield threshold.
    If this ship has at least one shield facing where either:
        - The shield facing's remaining points is less than the base shield threshold
        OR
        - The shield facing's percentage of remaining points (out of its maximum
        possible points) is less than the base shield threshold divided by 100 points
    then the ship will surrender when asked.
    """
    # brave/cowardly must be set before calling _get_random_base_shield_threshold
    # because the latter depends on the former
    brave, cowardly = _get_random_brave_or_cowardly()
    set_brave_or_cowardly(ship_id, brave=brave, cowardly=cowardly)
    
    threshold = _get_random_base_shield_threshold(ship_id)
    set_base_shield_threshold_for_surrender(ship_id, threshold)

def _get_random_brave_or_cowardly():
    """
    Returns brave, cowardly (both booleans).
    Picked randomly. Chances determined by _CHANCE_BRAVE and _CHANCE_COWARDLY.
    """
    random_value = random()
    brave = random_value < _CHANCE_BRAVE
    cowardly = 1 - _CHANCE_COWARDLY <= random_value
    return brave, cowardly

def _get_random_base_shield_threshold(ship_id, is_never_surrender_possible=True):
    """
    Returns a random base shield threshold for surrender (float).
    See _get_base_shield_threshold_for_surrender()'s description for details.
    Might return _BASE_SHIELD_THRESHOLD_FOR_SURRENDER_NEVER_VALUE, unless
    is_never_surrender_possible is passed as False.
    Never-surrender chance is determined by _get_chance_never_surrender, and
    the base shield threshold is chosen with a uniform probability distribution
    across the range returned from _get_base_shield_threshold_for_surrender_range.
    """
    if is_never_surrender_possible and random() < _get_chance_never_surrender(ship_id):
        return _BASE_SHIELD_THRESHOLD_FOR_SURRENDER_NEVER_VALUE
    else:
        shield_threshold_min, shield_threshold_max = _get_base_shield_threshold_for_surrender_range(ship_id)
        return randrange(shield_threshold_min, shield_threshold_max)

def override_surrender_conditions(ship_id, brave=False, cowardly=False, never_surrender=None, base_shield_threshold=None):
    """
    Manually sets the conditions (if any) under which a specific ship will surrender if asked.
    
    Calling this will completely replace the conditions that were randomly
    determined by a previous call of setup_surrender_conditions.
    For example, if a ship was randomly chosen to be brave in
    setup_surrender_conditions, and next override_surrender_conditions is called for
    it with a base_shield_threshold passed but not is_brave or is_cowardly passed,
    then that ship will no longer be considered brave.
    Or if a ship was randomly assigned a base shield threshold of 10 in
    setup_surrender_conditions, and next override_surrender_conditions is called
    for it with is_cowardly passed as True but base_shield_threshold is not passed,
    then its base shield threshold will be reassigned to some random value between
    30 and 50 (because that's the threshold range for cowardly ships).
    
    Note that this function allows for conditions that are not possible via
    the normal random setup in setup_surrender_conditions. For example, you can have
    a cowardly captain that never surrenders, or a ship with a base shield threshold
    of 100 meaning it will surrender the first time it's asked no matter its shields.
    So just watch out for combinations of arguments that you think would be confusing
    for players, or are otherwise unreasonable.
    (There might be some niche use cases for weird surrendering conditions that I don't
    know about, so I wanted to err on the side of allowing them.)
    
    Args:
        ship_id (int): id of the enemy ship
        brave (bool | None): Default False. Set to True to make the ship's
            captain brave. Note that it is not valid to have a captain that is
            both brave and cowardly.
        cowardly (bool | None): Default False. Set to True to make the ship's
            captain cowardly. Note that it is not valid to have a captain that is
            both brave and cowardly.
        never_surrender (bool | None): Defaults to a random value determined
            the same way as in setup_surrender_conditions, based on the new is_brave
            and is_cowardly values.
            Set to True to make the ship's captain never surrender.
        base_shield_threshold (float | None): Defaults to a random value determined
            the same way as in setup_surrender_conditions, based on the new is_brave
            and is_cowardly values.
            If never_surrender is passed as True, then this is not applicable, and
            therefore is ignored.
            Recommended values are between 10 and 50.
            See _get_base_shield_threshold_for_surrender()'s description for details.
    """
    # brave/cowardly must be set before calling _get_random_base_shield_threshold
    set_brave_or_cowardly(ship_id, brave=brave, cowardly=cowardly)
    
    if never_surrender is True:
        base_shield_threshold = _BASE_SHIELD_THRESHOLD_FOR_SURRENDER_NEVER_VALUE
    elif base_shield_threshold is None:
        base_shield_threshold = _get_random_base_shield_threshold(ship_id, is_never_surrender_possible=never_surrender is None)
    set_base_shield_threshold_for_surrender(ship_id, base_shield_threshold)

def has_surrender_conditions_set_up(ship_id):
    """
    Returns True if either setup_surrender_conditions or override_surrender_conditions
    has been called for this ship at least once, otherwise False.
    """
    return _get_base_shield_threshold_for_surrender(ship_id) is not None

def is_brave(ship_id):
    """Returns True if this ship's captain is brave, otherwise False."""
    return get_inventory_value(ship_id, _INVENTORY_KEY_IS_BRAVE_OR_COWARDLY) == BraveOrCowardlyValue.BRAVE

def is_cowardly(ship_id):
    """Returns True if this ship's captain is cowardly, otherwise False."""
    return get_inventory_value(ship_id, _INVENTORY_KEY_IS_BRAVE_OR_COWARDLY) == BraveOrCowardlyValue.COWARDLY

def set_brave_or_cowardly(ship_id, brave=False, cowardly=False):
    """
    Sets whether this ship's captain is brave, cowardly, or neither.
    It is not valid to have a captain that is both brave and cowardly.
    """
    if brave:
        brave_or_cowardly_value = BraveOrCowardlyValue.BRAVE
    elif cowardly:
        brave_or_cowardly_value = BraveOrCowardlyValue.COWARDLY
    else:
        brave_or_cowardly_value = BraveOrCowardlyValue.NEITHER
    set_inventory_value(ship_id, _INVENTORY_KEY_IS_BRAVE_OR_COWARDLY, brave_or_cowardly_value)

def will_never_surrender(ship_id):
    """
    Returns True if the ship will never surrender (regardless of whether it
    has told this fact to any player ship), otherwise False
    """
    return _get_base_shield_threshold_for_surrender(ship_id) == _BASE_SHIELD_THRESHOLD_FOR_SURRENDER_NEVER_VALUE

def _get_base_shield_threshold_for_surrender(ship_id):
    """
    Returns the base shield threshold for this ship to surrender.
    
    Each enemy ship that can be surrendered gets assigned a base shield
    threshold when it spawns.
    If this ship has at least one shield facing where either:
        - The shield facing's remaining points is less than the base shield threshold
        OR
        - The shield facing's percentage of remaining points (out of its maximum
        possible points) is less than the base shield threshold divided by 100 points
    then the ship will surrender when asked.
    
    For ships that will never surrender, this function returns
    _BASE_SHIELD_THRESHOLD_FOR_SURRENDER_NEVER_VALUE. You should probably
    use the will_never_surrender() function to detect these ships.
    """
    return get_inventory_value(ship_id, _INVENTORY_KEY_BASE_SHIELD_THRESHOLD_FOR_SURRENDER)

def set_base_shield_threshold_for_surrender(ship_id, threshold):
    """
    Sets the base shield threshold for this ship to surrender.
    See _get_base_shield_threshold_for_surrender()'s description for details.
    """
    set_inventory_value(ship_id, _INVENTORY_KEY_BASE_SHIELD_THRESHOLD_FOR_SURRENDER, threshold)

def has_declared_never_surrender(ship_id):
    """
    Returns True if the ship has told at least one player that this ship
    will never surrender, otherwise False
    """
    return has_role(ship_id, _ROLE_KEY_NEVER_SURRENDER)

def _set_declared_never_surrender(ship_id):
    """
    Call this to indicate the ship has told at least one player that this ship
    will never surrender
    """
    add_role(ship_id, _ROLE_KEY_NEVER_SURRENDER)

# ----- Player surrender requests -----

def test_surrenderable(ship_object, player_ship_object):
    """
    Determines what would happen if the player ship asked another ship to
    surrender. Does not actually perform the action of sending the surrender
    request.
    
    A surrender attempt would succeed if and only if all of the following are ture:
        - The ship is not already surrendered
        - The ship and player ship are at least 5000 units apart
        - The ship is not "never-surrender", i.e. it wouldn't refuse to surrender
        even if its shields were all gone
        - The ship has at least one shield facing where either:
            - The shield facing's remaining points is less than the base shield
            threshold
            OR
            - The shield facing's percentage of remaining points (out of its
            maximum possible points) is less than the base shield threshold
            divided by 100 points
        
    The case where a ship type has zero shield facings is not handled very well;
    the result will only ever be either 'no_too_far' or 'never'. If information
    about the ship's internal damage state can be read by mission scripts, then
    this behavior could be improved.
    
    Args:
        ship_object (ship object): the ship that would be asked to surrender
        player_ship_object (ship object): the player ship that would be sending
            the surrender request
    Returns:
        What would happen if the player ship asked this ship to surrender,
        in the form of a value returned by one of the following functions:
        (This is essentially an enum that's mast-compatible)
        surrender_attempt_result_yes()
        surrender_attempt_result_no_too_far()
        surrender_attempt_result_no()
        surrender_attempt_result_not_yet()
        surrender_attempt_result_never()
        surrender_attempt_result_already_surrendered()
    """
    
    # Keep in mind this kind of race condition is possible:
    # 1) The server (correctly) tells the comms officer's client that
    #    a ship hasn't surrendered yet
    # 2) The comms officer selects the surrender button, and at around
    #    the same time the server actually surrenders the vessel (either
    #    triggered by another player ship or maybe from the same comms
    #    client spamming surrender requests)
    # 3) The server recieves the message from the comms officer's client
    #    telling it to attempt to surrender the ship
    # Therefore, re-check conditions even if they would cause the surrender
    # or code case buttons to hide.
    if has_surrendered(ship_object.id):
        return surrender_attempt_result_already_surrendered()
    
    if is_distance_farther_than_or_equal_to(ship_object.pos, player_ship_object.pos, _RADIUS_CLOSE_ENOUGH_FOR_SURRENDER):
        return surrender_attempt_result_no_too_far()
    
    base_shield_threshold = _get_base_shield_threshold_for_surrender(ship_object.id)
    never_surrender = base_shield_threshold == _BASE_SHIELD_THRESHOLD_FOR_SURRENDER_NEVER_VALUE
    
    # min and max here are the absolutes across all possible ships
    # (not the min and max for this ship)
    has_shield_under_threshold_max = False
    has_shield_under_threshold = False
    has_shield_under_threshold_min = False
    shield_count = ship_object.data_set.get("shield_count", 0)
    if shield_count == 0:
        # Ship type has no shields
        # TODO handle this better if it's possible to check hull points/armor
        # https://github.com/orgs/artemis-sbs/discussions/500
        return surrender_attempt_result_never()
    
    for i in range(shield_count):
        max_shield_points = ship_object.data_set.get("shield_max_val", i)
        current_shield_points = ship_object.data_set.get("shield_val", i)
        
        if _is_below_points_and_percentage(current_shield_points, max_shield_points, _BASE_SHIELD_THRESHOLD_FOR_SURRENDER_MAX):
            has_shield_under_threshold_max = True
            if _is_below_points_and_percentage(current_shield_points, max_shield_points, base_shield_threshold):
                has_shield_under_threshold = True
            if _is_below_points_and_percentage(current_shield_points, max_shield_points, _BASE_SHIELD_THRESHOLD_FOR_SURRENDER_MIN):
                has_shield_under_threshold_min = True
    
    if not never_surrender and has_shield_under_threshold:
        return surrender_attempt_result_yes()
    elif never_surrender and has_shield_under_threshold_min:
        return surrender_attempt_result_never()
    elif has_shield_under_threshold_max:
        return surrender_attempt_result_not_yet()
    else:
        return surrender_attempt_result_no()

def _is_below_points_and_percentage(shield_points, max_shield_points, threshold):
    """
    Returns True if shield_points < threshold
    OR shield_points / max_shield_points < threshold / 100.
    Otherwise, returns False.
    """
    return shield_points < min(threshold, 0.01 * threshold * max_shield_points)

def attempt_surrender(ship_object, player_ship_object):
    """
    Makes the player ship ask another ship to surrender. If successful, surrenders
    that ship.
    
    Success is determined by the test_surrenderable function; see its
    description for details on what determines success/failure.
    
    Regardless of success, a comms message is sent to the player ship that
    describes the outcome by calling the send_comms_response function;
    see its description for details.
    
    Args:
        ship_object (ship object): the ship that is being asked to surrender
        player_ship_object (ship object): the player ship that is sending
            the surrender request
    Returns:
        The result of the attempt, in the form of a value returned by one of
        the following functions:
        (This is essentially an enum that's mast-compatible)
        surrender_attempt_result_yes()
        surrender_attempt_result_no_too_far()
        surrender_attempt_result_no()
        surrender_attempt_result_not_yet()
        surrender_attempt_result_never()
        surrender_attempt_result_already_surrendered()
    """
    surrender_attempt_result = test_surrenderable(ship_object, player_ship_object)
    if surrender_attempt_result == surrender_attempt_result_yes():
        _set_surrendered(ship_object, player_ship_object)
    elif surrender_attempt_result == surrender_attempt_result_never():
        _set_declared_never_surrender(ship_object.id)
    send_comms_response(ship_object.id, player_ship_object, surrender_attempt_result)
    return surrender_attempt_result

# ----- Secret Code Case -----

def test_code_caseable(ship_object, player_ship_object):
    """
    Determines what would happen if the player ship attempted to use a code case
    on another ship. Does not actually perform the action of using a code case.
    
    A code case attempt would succeed if and only if all of the following are true:
        - The ship is not already surrendered
        - The player ship has at least one available code case
        - The ship and player ship are at least 5000 units apart
    
    Notably, if the ship would never surrender via normal player request,
    that's okay; code cases would still work.
    
    Args:
        ship_object (ship object): the ship that would be forced to surrender
        player_ship_object (ship object): the player ship that would attempt
            to use a code case
    Returns:
        What would happen if the player ship attempted to code case this ship,
        in the form of a value returned by one of the following functions:
        (This is essentially an enum that's mast-compatible)
        code_case_attempt_result_success()
        code_case_attempt_result_fail_too_far()
        code_case_attempt_result_already_surrendered()
        code_case_attempt_result_player_has_no_code_cases()
    """
    
    # Keep in mind this kind of race condition is possible:
    # 1) The server (correctly) tells the comms officer's client that
    #    a ship hasn't surrendered yet
    # 2) The comms officer selects the surrender button, and at around
    #    the same time the server actually surrenders the vessel (either
    #    triggered by another player ship or maybe from the same comms
    #    client spamming surrender requests)
    # 3) The server recieves the message from the comms officer's client
    #    telling it to attempt to surrender the ship
    # Therefore, re-check conditions even if they would cause the surrender
    # or code case buttons to hide.
    if has_surrendered(ship_object.id):
        return code_case_attempt_result_already_surrendered()
    
    if not has_code_case(player_ship_object.id):
        return code_case_attempt_result_player_has_no_code_cases()
    
    if is_distance_farther_than_or_equal_to(ship_object.pos, player_ship_object.pos, _RADIUS_CLOSE_ENOUGH_FOR_CODE_CASE):
        return code_case_attempt_result_fail_too_far()
    
    return code_case_attempt_result_success()

def attempt_code_case(ship_object, player_ship_object):
    """
    If valid, makes the player ship use a code case on the other ship,
    causing that ship to surrender.
    
    Success is determined by the test_code_caseable function; see its
    description for details on what determines success/failure
    
    Regardless of success, a comms message is sent to the player ship that
    describes the outcome by calling the send_comms_response function;
    see its description for details.
    
    Args:
        ship_object (ship object): the ship that might be forced to surrender
        player_ship_object (ship object): the player ship that is attempting
            to use a code case
    Returns:
        The result of the attempt, in the form of a value returned by one of
        the following functions:
        (This is essentially an enum that's mast-compatible)
        code_case_attempt_result_success()
        code_case_attempt_result_fail_too_far()
        code_case_attempt_result_already_surrendered()
        code_case_attempt_result_player_has_no_code_cases()
    """
    code_case_attempt_result = test_code_caseable(ship_object, player_ship_object)
    if code_case_attempt_result == code_case_attempt_result_success():
        _set_surrendered(ship_object, player_ship_object, via_code_case=True)
        _consume_code_case(player_ship_object.id)
    send_comms_response(ship_object.id, player_ship_object, code_case_attempt_result)
    return code_case_attempt_result

def has_code_case(player_ship_id):
    """
    Returns True if the player ship has at least one secret code case,
    otherwise False
    """
    return get_inventory_value(player_ship_id, _INVENTORY_KEY_CODE_CASE_COUNT, 0) > 0

def _consume_code_case(player_ship_id):
    """
    Consumes one code case from the player ship
    Does not check whether it is valid to do so
    """
    code_case_count = get_inventory_value(player_ship_id, _INVENTORY_KEY_CODE_CASE_COUNT, 0)
    set_inventory_value(player_ship_id, _INVENTORY_KEY_CODE_CASE_COUNT, code_case_count - 1)

def is_code_cased(ship_id):
    """
    Returns True if the ship has surrendered because a secret code case
    was used on it, otherwise False
    """
    return get_inventory_value(ship_id, _INVENTORY_KEY_IS_CODE_CASE_SURRENDER) is not None

# ----- Comms -----

def send_comms_response(ship_id, player_ship_object, attempt_result):
    """ Sends a comms message in response to a surrender or code case attempt """
    
    set_variable("COMMS_ORIGIN_ID", player_ship_object.id)
    set_variable("COMMS_SELECTED_ID", ship_id)
    surrender_color = get_shared_variable("surrender_color", "yellow")
    raider_color = get_shared_variable("raider_color", "red")
    
    if attempt_result == surrender_attempt_result_yes():
        comms_receive(f"Curse you, {player_ship_object.name}, you've won this time! We surrender and will retreat!", title="Surrendered", title_color=surrender_color)
    elif attempt_result == surrender_attempt_result_no() or attempt_result == surrender_attempt_result_no_too_far():
        comms_receive(f"Go climb a tree, {player_ship_object.name}!", title="Surrender request ignored", title_color=raider_color)
    elif attempt_result == surrender_attempt_result_not_yet():
        comms_receive(f"Hah, you haven't beaten us yet, {player_ship_object.name}!", title="Surrender request ignored", title_color=raider_color)
    elif attempt_result == surrender_attempt_result_never():
        comms_receive("Surrender? Never!", title="Never Surrender", title_color=raider_color)
    elif attempt_result == surrender_attempt_result_already_surrendered():
        comms_receive("We've already surrendered.", title="Already Surrendered", title_color=surrender_color)
    elif attempt_result == code_case_attempt_result_success():
        comms_receive(f"This is Agent XK3. I've assumed control of this ship and will steer it out of the battle. Good luck, {player_ship_object.name}.", title="Surrendered", title_color=surrender_color)
    elif attempt_result == code_case_attempt_result_fail_too_far():
        comms_receive_internal(f"We're too far to transmit the secret codes. Our secure comms are only effective within a range of about {_RADIUS_CLOSE_ENOUGH_FOR_CODE_CASE}.", title="Too Far to Transmit", title_color=surrender_color)
    elif attempt_result == code_case_attempt_result_already_surrendered():
        comms_receive(f"This is Agent XK3. This ship has already surrendered, so keep these codes to use on another ship. Good luck out there, {player_ship_object.name}.", title="Already Surrendered", title_color=surrender_color)
    elif attempt_result == code_case_attempt_result_player_has_no_code_cases():
        comms_receive_internal("We don't have any secret code cases left.", title="No Code Cases", title_color=surrender_color)
    
    comms_navigate("//comms")

# ----- Quasi-enums -----

# Use functions to allow these to be easily accessed from MAST code

def surrender_attempt_result_yes():
    return 1
def surrender_attempt_result_no_too_far():
    return 2
def surrender_attempt_result_no():
    return 3
def surrender_attempt_result_not_yet():
    return 4
def surrender_attempt_result_never():
    return 5
def surrender_attempt_result_already_surrendered():
    return 6

def code_case_attempt_result_success():
    return 7
def code_case_attempt_result_fail_too_far():
    return 8
def code_case_attempt_result_already_surrendered():
    return 9
def code_case_attempt_result_player_has_no_code_cases():
    return 10

# ----- Technical Constants; you probably don't want to change these -----

_BASE_SHIELD_THRESHOLD_FOR_SURRENDER_NEVER_VALUE = -1
_INVENTORY_KEY_IS_CODE_CASE_SURRENDER = "code_case_surr"
_INVENTORY_KEY_BASE_SHIELD_THRESHOLD_FOR_SURRENDER = "surr_shld_thresh"
_INVENTORY_KEY_IS_BRAVE_OR_COWARDLY = "brv_cwrd"

class BraveOrCowardlyValue(Enum):
    BRAVE = 1
    COWARDLY = 2
    NEITHER = 3

# DO NOT CHANGE
# these values are used by places in the code that do not reference these variables
_ROLE_KEY_SURRENDERED = "surrendered"
_ROLE_KEY_NEVER_SURRENDER = "never_surrender"
_INVENTORY_KEY_CODE_CASE_COUNT = "secret_codecase"

# -----

# Copied from fleets/map_common.py
# The vanilla code calls this from mast, which apparently ignores import requirements.
# This can't be imported to any python in this /comms/ folder because 'fleets' comes
# after 'comms' alphabetically.
# It also doesn't make a lot of sense to move just this function to _lib since it's
# tightly bound to other functions in map_common.py, and moving everything doesn't
# seem worthwhile for such a big deviation from the vanilla codebase.
from sbs_utils.procedural.query import to_id
from sbs_utils.procedural.inventory import get_inventory_value
from sbs_utils.procedural.links import unlink
def fleet_remove_ship(id_or_obj):
    ship_id = to_id(id_or_obj)
    if ship_id is None:
        return
    fleet_id = get_inventory_value(ship_id, "my_fleet_id")
    unlink(fleet_id,"ship_list", ship_id)
