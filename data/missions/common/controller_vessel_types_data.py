from sbs_utils.fs import load_yaml_string
from sbs_utils.procedural.execution import get_shared_variable, set_shared_variable
from sbs_utils.procedural.grid import grid_get_grid_data
from sbs_utils.procedural.media import media_read_relative_file
from sbs_utils.procedural.ship_data import get_ship_data

from data.missions.common.model_single_seat_craft_type import CraftCategory, get_craft_category, SingleSeatCraftType
from data.missions.common.model_player_capital_ship_type import PlayerCapitalShipType
from data.missions.common.model_vessel_type import Beam
from data.missions.common.model_vessel_types_data import VesselTypesData

def initialize_vessel_types_data():
    all_ship_types_list = get_ship_data()["#ship-list"]
    
    # ----- First look for single-seat craft -----
    
    craft_types_by_key = {}
    for ship_type_data in all_ship_types_list:
        if "roles" not in ship_type_data:
            continue
        roles = ship_type_data["roles"]
        if "cockpit" not in roles:
            continue
        category = get_craft_category(roles)
        if category is None:
            continue
        
        single_seat_craft_type = _create_single_seat_craft_type_from_data(ship_type_data)
        
        craft_types_by_key[single_seat_craft_type.ship_type_key] = single_seat_craft_type
    
    # ----- Then what single-seat craft types each origin uses -----
    
    origin_to_single_seat_craft_types = {}
    # Use these defaults if origin isn't in hangar_crafts.yaml
    # or if hangar_crafts.yaml can't be loaded for some reason
    default_single_seat_craft_types = {CraftCategory.SHUTTLE.value: "tsn_shuttle", CraftCategory.FIGHTER.value: "tsn_fighter", CraftCategory.BOMBER.value: "tsn_bomber"}
    
    # Note the dependency on the hangar folder. It might not be present
    # in other mission scripts.
    # Maybe move hangar_crafts.yaml into this folder? But that would
    # just create the same problem in the hangar.py code instead.
    # TODO see if this ^ can be handled better.
    origin_to_single_seat_craft_types_data = load_yaml_string(media_read_relative_file("../hangar/hangar_crafts.yaml"))
    if origin_to_single_seat_craft_types_data is not None:
        for origin, single_seat_craft_types_data in origin_to_single_seat_craft_types_data.items():
            single_seat_craft_types = {}
            for single_seat_craft_type_data in single_seat_craft_types_data:
                roles = single_seat_craft_type_data["roles"]
                craft_category = get_craft_category(roles)
                if craft_category is None:
                    # can't use this uncategorized craft type
                    continue
                ship_type_key = single_seat_craft_type_data["key"]
                single_seat_craft_types[craft_category.value] = ship_type_key
            origin_to_single_seat_craft_types[origin] = single_seat_craft_types
    
    # ----- Then what ship types have an internal ship grid -----
    
    internal_ship_grids_by_ship_type_key = {
    ship_type_key: ship_grid_data["grid_objects"] for ship_type_key, ship_grid_data in grid_get_grid_data().items() if "grid_objects" in ship_grid_data and len(ship_grid_data["grid_objects"]) > 0}
    
    # ----- And finally capital player ships -----
    
    ship_types_by_key = {}
    # build dictionary by origin + name because that's what the drop downs
    # have to use. If there's two ship types with the same origin and name,
    # then only one will be used.
    ship_types_by_origin_and_name = {}
    ship_type_names_by_origin = {}
    
    for ship_type_data in all_ship_types_list:
        if "roles" not in ship_type_data:
            continue
        roles = ship_type_data["roles"]
        if "ship" not in roles:
            continue
        ship_type_key = ship_type_data["key"]
        if ship_type_key not in internal_ship_grids_by_ship_type_key:
            continue
        internal_ship_grid_dict = internal_ship_grids_by_ship_type_key[ship_type_key]
        
        ship_type = _create_player_capital_ship_type_from_data(ship_type_data, origin_to_single_seat_craft_types, default_single_seat_craft_types, internal_ship_grid_dict)
        
        if (ship_type.origin, ship_type.ship_type_name) in ship_types_by_origin_and_name:
            other_ship_type = ship_types_by_origin_and_name[(ship_type.origin, ship_type.ship_type_name)]
            print(f"WARNING: there are multiple entries in shipData.yaml for a ship with origin '{ship_type.origin}' and name '{ship_type.ship_type_name}'. Only '{other_ship_type.ship_type_key}' will be selectable for player ships. '{ship_type.ship_type_key}' will not be.")
            continue
        
        ship_types_by_key[ship_type.ship_type_key] = ship_type
        
        ship_types_by_origin_and_name[(ship_type.origin, ship_type.ship_type_name)] = ship_type
        
        if ship_type.origin not in ship_type_names_by_origin:
            ship_type_names_by_origin[ship_type.origin] = []
        ship_type_names_by_origin[ship_type.origin].append(ship_type.ship_type_name)
    
    ship_type_name_csvs_by_origin = {}
    for origin, ship_types_list in ship_type_names_by_origin.items():
        ship_type_name_csvs_by_origin[origin] = ",".join(ship_types_list)
    
    VESSEL_TYPES_DATA = VesselTypesData(craft_types_by_key, ship_types_by_key, ship_types_by_origin_and_name, ship_type_name_csvs_by_origin)
    
    _set_vessel_types_data(VESSEL_TYPES_DATA)

def _parse_vessel_properties_from_data(ship_type_data):
    ship_type_key = ship_type_data["key"]
    ship_type_name = ship_type_data["name"]
    origin = ship_type_data["origin"]
    description = ship_type_data["long_desc"]
    
    max_ordinance_counts = {}
    if "torpedostart" in ship_type_data:
        for ordinance_data in ship_type_data["torpedostart"]:
            for ordinance_type, max_count in ordinance_data.items():
                max_ordinance_counts[ordinance_type] = max_count
    
    turn_rate = ship_type_data["turn_rate"]
    speed_coeff = ship_type_data["speed_coeff"]
    scan_strength_coeff = ship_type_data["scan_strength_coeff"]
    roles = ship_type_data["roles"]
    shields = ship_type_data["shields"]
    hullpoints = ship_type_data["hullpoints"]
    
    beams = []
    if "hull_port_sets" in ship_type_data and "beam Primary Beams" in ship_type_data["hull_port_sets"]:
        for beam_data in ship_type_data["hull_port_sets"]["beam Primary Beams"]:
            cycle_time = beam_data["cycle_time"]
            damage_coeff = beam_data["damage_coeff"]
            beam_range = beam_data["range"]
            arcwidth = beam_data["arcwidth"]
            # For some reason *just* the tsn_heavy_cruiser has two beams
            # with their `barrel_angle`s commented out.
            # Default these barrel angles to zero, I guess.
            if "barrel_angle" in beam_data:
                barrel_angle = beam_data["barrel_angle"]
            else:
                barrel_angle = 0
            beams.append(Beam(cycle_time, damage_coeff, beam_range, arcwidth, barrel_angle))
    beams = sorted(beams, reverse=True)
    
    return ship_type_key, ship_type_name, origin, description, max_ordinance_counts, turn_rate, speed_coeff, scan_strength_coeff, roles, shields, hullpoints, beams
    
def _create_single_seat_craft_type_from_data(ship_type_data):
    ship_type_key, ship_type_name, origin, description, max_ordinance_counts, turn_rate, speed_coeff, scan_strength_coeff, roles, shields, hullpoints, beams = _parse_vessel_properties_from_data(ship_type_data)
    
    category = get_craft_category(roles)
    
    return SingleSeatCraftType(ship_type_key, ship_type_name, origin, description, max_ordinance_counts, turn_rate, speed_coeff, scan_strength_coeff, roles, shields, hullpoints, beams, category)

def _create_player_capital_ship_type_from_data(ship_type_data, origin_to_single_seat_craft_types, default_single_seat_craft_types, internal_ship_grid_dict):
    ship_type_key, ship_type_name, origin, description, max_ordinance_counts, turn_rate, speed_coeff, scan_strength_coeff, roles, shields, hullpoints, beams = _parse_vessel_properties_from_data(ship_type_data)
    
    tube_count = ship_type_data["tubecount"]
    ship_energy_cost = ship_type_data["ship_energy_cost"]
    warp_energy_cost = ship_type_data["warp_energy_cost"]
    jump_energy_cost = ship_type_data["jump_energy_cost"]
    
    has_warp_drive, has_jump_drive = _get_drives_in_internal_ship_grid(internal_ship_grid_dict)
    
    if origin in origin_to_single_seat_craft_types:
        single_seat_craft_types = origin_to_single_seat_craft_types[origin]
    else:
        single_seat_craft_types = default_single_seat_craft_types
    
    single_seat_craft_counts = _get_single_seat_craft_counts(internal_ship_grid_dict)
    
    return PlayerCapitalShipType(ship_type_key, ship_type_name, origin, description, max_ordinance_counts, turn_rate, speed_coeff, scan_strength_coeff, roles, shields, hullpoints, beams, tube_count, has_warp_drive, has_jump_drive, ship_energy_cost, warp_energy_cost,jump_energy_cost, single_seat_craft_types, single_seat_craft_counts)

def _get_drives_in_internal_ship_grid(internal_ship_grid_dict):
    has_warp_drive = False
    has_jump_drive = False
    for node in internal_ship_grid_dict:
        if "jump" in node["roles"]:
            has_jump_drive = True
            if has_warp_drive:
                return has_warp_drive, has_jump_drive
        if "warp" in node["roles"]:
            has_warp_drive = True
            if has_jump_drive:
                return has_warp_drive, has_jump_drive
    return has_warp_drive, has_jump_drive

def _get_single_seat_craft_counts(internal_ship_grid_dict):
    single_seat_craft_counts = {}
    for category in CraftCategory:
        single_seat_craft_counts[category.value] = 0
    for node in internal_ship_grid_dict:
        for category in CraftCategory:
            if category.value in node["roles"]:
                single_seat_craft_counts[category.value] += 1
    return single_seat_craft_counts

# ---- setter/getter wrappers -----

def _set_vessel_types_data(vessel_types_data):
    set_shared_variable(_VESSEL_TYPES_DATA_VAR_NAME, vessel_types_data)

def get_vessel_types_data():
    return get_shared_variable(_VESSEL_TYPES_DATA_VAR_NAME)

_VESSEL_TYPES_DATA_VAR_NAME = "_vessel_types_data"
