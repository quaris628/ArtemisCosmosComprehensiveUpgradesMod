"""
Supporting functions for comms messages and menus to allow interactions between
player ships and surrendered ships which are related to the player telling
surrendered ships where to go.
The effects of these navigation commands are mainly handed by code in
surrendered_navigation.py and surrendered_navigation.mast.
"""

from sbs_utils.procedural.query import to_object
from surrendered_navigation import get_nav_state, nav_state_to_spawnpoint_no_deletion, nav_state_to_spawnpoint_deletion_ok, nav_state_running_away_no_deletion, nav_state_running_away_deletion_ok, nav_state_commanded_to_stop, nav_state_commanded_to_location, nav_state_commanded_to_follow_ship, get_commanded_follow_ship_id

# returns [message, special code]
# mast doesn't support multiple return values,
# so return a single list of values instead
# valid special codes are:
# - None
# - hail_message_nav_state_component_special_error()
# - hail_message_nav_state_component_special_run_away()
def get_hail_message_nav_state_component(ship_id):
    nav_state = get_nav_state(ship_id)
    if nav_state == nav_state_to_spawnpoint_no_deletion() or nav_state == nav_state_to_spawnpoint_deletion_ok():
        return ["We are retreating out of this sector.", None]
    elif nav_state == nav_state_running_away_no_deletion() or nav_state == nav_state_running_away_deletion_ok():
        return [None, hail_message_nav_state_component_special_run_away()]
    elif nav_state == nav_state_commanded_to_stop():
        return ["We are holding our position.", None]
    elif nav_state == nav_state_commanded_to_location():
        return ["We are navigating to the requested location.", None]
    elif nav_state == nav_state_commanded_to_follow_ship():
        following_ship_object = to_object(get_commanded_follow_ship_id(ship_id))
        if following_ship_object is None:
            return ["We were following a ship, but it was destroyed.", None]
        else:
            return [f"We are following {following_ship_object.name}.", None]
    else:
        return ["", hail_message_nav_state_component_special_error()]

def hail_message_nav_state_component_special_error():
    return 1

def hail_message_nav_state_component_special_run_away():
    return 2
