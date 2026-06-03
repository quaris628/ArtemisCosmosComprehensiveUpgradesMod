from sbs_utils.procedural.query import to_object
from sbs_utils.procedural.roles import has_role, has_roles, all_roles
from sbs_utils.procedural.comms import comms_broadcast
from sbs_utils.procedural.grid import grid_objects
from sbs_utils.procedural.signal import signal_emit
from sbs import get_hull_map

def color_repair_status_background_full():
    return "#007f00a0"
def color_repair_status_background_minor_damage():
    return "#cc6600cc"
def color_repair_status_background_major_damage():
    return "#cc0000ff"
def color_repair_status_background_zero():
    return "#000000ff"

def system_roles_beams():
    return "system,weapon,beam"
def system_roles_torpedoes():
    return "system,weapon,torpedo"
def system_roles_impulse():
    return "system,engine,impulse"
def system_roles_warp():
    return "system,engine,warp"
def system_roles_jump():
    return "system,engine,jump"
def system_roles_maneuver():
    return "system,engine,maneuver"
def system_roles_sensors():
    return "system,sensor"
def system_roles_front_shield():
    return "system,shield,fwd"
def system_roles_rear_shield():
    return "system,shield,aft"

def system_roles_special_warp_and_jump():
    return "special-warp-and-jump"

def is_warp_or_jump(system_roles):
    return system_roles == system_roles_warp() or system_roles == system_roles_jump()

def get_set_of_each_system_roles():
    return { system_roles_beams(), system_roles_torpedoes(), system_roles_impulse(), system_roles_warp(), system_roles_jump(), system_roles_maneuver(), system_roles_sensors(), system_roles_front_shield(), system_roles_rear_shield() }

def get_system_roles(node_id):
    for system_roles in get_set_of_each_system_roles():
        if has_roles(node_id, system_roles):
            return system_roles
    return None

def update_repair_level_display_text_and_style(player_ship_id, system_roles, text, background_color):
    signal_emit("update_repair_level_text_on_ship_" + str(player_ship_id), data={"PLAYER_SHIP_ID": player_ship_id, "SYSTEM_ROLES": system_roles, "TEXT": text, "BACKGROUND_COLOR": background_color})

# returns text, background_color
def get_repair_level_display_text_and_style(undamaged_nodes_count, total_nodes_count, is_unknown):
    if is_unknown:
        return "?", color_repair_status_background_zero()
    if total_nodes_count == 0:
        return "N/A", color_repair_status_background_zero()
    
    repair_level_percentage = undamaged_nodes_count / total_nodes_count * 100
    display_text = f"{repair_level_percentage:.0f}%"
    
    if undamaged_nodes_count == total_nodes_count:
        background_color = color_repair_status_background_full()
    elif undamaged_nodes_count == 0:
        background_color = color_repair_status_background_zero()
    elif undamaged_nodes_count * 2 < total_nodes_count: # 0 < repair level < 50%
        background_color = color_repair_status_background_major_damage()
    else: # 50% <= repair level < 100%
        background_color = color_repair_status_background_minor_damage()
    
    return display_text, background_color

# returns a dict like { system_roles: [ grid_object_id_1, grid_object_id_2, ...], ...}
def get_system_grid_object_ids(player_ship_id, systems_filter):
    all_player_ship_grid_object_ids = grid_objects(player_ship_id)
    
    system_grid_object_ids = {}
    for system_roles in systems_filter:
        system_grid_object_ids[system_roles] = all_player_ship_grid_object_ids & all_roles(system_roles)
    
    return system_grid_object_ids

# returns 1 if damaged, 0 if not damaged, -1 if cannot be determined
def is_system_grid_object_damaged(system_grid_object_id):
    if has_role(system_grid_object_id, "__damaged__"):
        return 1
    elif has_role(system_grid_object_id, "__undamaged__"):
        return 0
    else:
        return -1 # unknown

# systems_filter is a set of the system tags that should be returned; default is all systems
def update_systems_repair_level(player_ship_id, systems_filter=get_set_of_each_system_roles()):
    
    system_grid_object_ids = get_system_grid_object_ids(player_ship_id, systems_filter)
    
    warp_and_jump_needs_update = False
    warp_and_jump_undamaged_nodes_count = 0
    warp_and_jump_total_nodes_count = 0
    warp_and_jump_is_unknown = False
    
    for system_roles in systems_filter:
        
        undamaged_nodes_count = 0
        total_nodes_count = 0
        is_unknown = False
        for system_grid_object_id in system_grid_object_ids[system_roles]:
            total_nodes_count += 1
            is_damaged = is_system_grid_object_damaged(system_grid_object_id)
            if is_damaged == 0: # not damaged
                undamaged_nodes_count += 1
            elif is_damaged == 1: # damaged:
                pass
            else: # cannot be determined
                is_unknown = True
                break
        
        if is_warp_or_jump(system_roles):
            # combine warp and jump systems repair levels into a single percentage
            # this should work regardless of whether the ship type is warp-only, jump-only, or has both warp and jump
            warp_and_jump_needs_update = True
            warp_and_jump_undamaged_nodes_count += undamaged_nodes_count
            warp_and_jump_total_nodes_count += total_nodes_count
            warp_and_jump_is_unknown = warp_and_jump_is_unknown or is_unknown
        else:
            text, background_color = get_repair_level_display_text_and_style(undamaged_nodes_count, total_nodes_count, is_unknown)
            update_repair_level_display_text_and_style(player_ship_id, system_roles, text, background_color)
    
    if warp_and_jump_needs_update:
        text, background_color = get_repair_level_display_text_and_style(warp_and_jump_undamaged_nodes_count, warp_and_jump_total_nodes_count, warp_and_jump_is_unknown)
        update_repair_level_display_text_and_style(player_ship_id, system_roles_special_warp_and_jump(), text, background_color)

def update_heat_pool_systems_repair_level(player_ship_id, heat_pool_id):
    if heat_pool_id == "0": # weapons
        systems_filter = { system_roles_beams(), system_roles_torpedoes() }
    elif heat_pool_id == "1": # engines
        systems_filter = { system_roles_impulse(), system_roles_warp(), system_roles_jump(), system_roles_maneuver() }
    elif heat_pool_id == "2": # sensors
        systems_filter = { system_roles_sensors() }
    elif heat_pool_id == "3": # shields
        systems_filter = { system_roles_front_shield(), system_roles_rear_shield() }
    else:
        return
    update_systems_repair_level(player_ship_id, systems_filter)

def update_repair_level_single_node(player_ship_id, node_id):
    system_roles = get_system_roles(node_id)
    if system_roles is None: # not a system node; it's a room
        return
    update_systems_repair_level(player_ship_id, systems_filter={system_roles})
