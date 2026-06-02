
from sbs_utils.procedural.execution import get_shared_variable, set_shared_variable
from sbs_utils.procedural.roles import has_role, has_roles, role, all_roles

# ----- Misc -----

def is_enemy(space_object_id):
    return has_role(space_object_id, "raider") or has_roles(space_object_id, "enemy,station")

def get_all_enemy_ids(except_enemy_id=None):
    all_enemy_ids = role("raider") | all_roles("enemy,station")
    all_enemy_ids.discard(except_enemy_id)
    return all_enemy_ids

# ----- Setter/getter wrappers -----

def reset_game_end_conditions():
    set_game_end_conditions(end_if_no_enemies=None, end_if_no_ally_stations=None)

# There's also a timer which can end the game. It's always respected if it's set.
# end_if_no_enemies default is True
# end_if_no_ally_stations default is True
# TODO also provide override for no player ships, e.g. for all-fighter custom mission script
# And/or maybe provide override for whether single-seat craft should count as player ships
# for the purposes of whether the game ends
def set_game_end_conditions(end_if_no_enemies=None, end_if_no_ally_stations=None):
    set_shared_variable(_IS_END_IF_NO_ENEMIES_ENABLED_VAR_NAME, end_if_no_enemies)
    set_shared_variable(_IS_END_IF_NO_ALLY_STATIONS_ENABLED_VAR_NAME, end_if_no_ally_stations)
 
def is_end_if_no_enemies_enabled():
    is_enabled = get_shared_variable(_IS_END_IF_NO_ENEMIES_ENABLED_VAR_NAME)
    if is_enabled is None:
        return True
    return is_enabled

def is_end_if_no_ally_stations_enabled():
    is_enabled = get_shared_variable(_IS_END_IF_NO_ALLY_STATIONS_ENABLED_VAR_NAME)
    if is_enabled is None:
        return True
    return is_enabled

_IS_END_IF_NO_ENEMIES_ENABLED_VAR_NAME = "_is_end_if_no_enemies_enabled"
_IS_END_IF_NO_ALLY_STATIONS_ENABLED_VAR_NAME = "_is_end_if_no_ally_stations_enabled"
