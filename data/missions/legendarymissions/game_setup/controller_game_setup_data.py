import sbs

from sbs_utils.faces import set_face, random_face
from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import AWAIT, END, get_variable, get_shared_variable, set_variable, set_shared_variable, task_schedule
from sbs_utils.procedural.extra_scan_sources import extra_scan_sources_schedule
from sbs_utils.procedural.gui.console_types import gui_get_console_type_list, gui_get_console_types
from sbs_utils.procedural.grid import grid_get_grid_current_theme, grid_set_grid_current_theme
from sbs_utils.procedural.internal_damage import grid_get_grid_data, grid_rebuild_grid_objects
from sbs_utils.procedural.inventory import set_inventory_value
from sbs_utils.procedural.maps import maps_get_list
from sbs_utils.procedural.roles import add_role
from sbs_utils.procedural.query import to_blob, to_space_object
from sbs_utils.procedural.settings import settings_get_defaults
from sbs_utils.procedural.signal import signal_emit
from sbs_utils.procedural.spawn import player_spawn
from sbs_utils.procedural.terrain import terrain_to_value
from sbs_utils.procedural.timers import delay_app, set_timer

from data.missions.common.controller_vessel_types_data import get_vessel_types_data

from model_console_slot import ConsoleSlot
from model_player_ship_setup_data import PlayerShipSetupData
from model_environment_setup_data import EnvironmentalFrequency, EnvironmentSetupData
from model_game_setup_data import GameSetupData

# ----- Initializing -----

@label()
def initialize_game_setup_data():
    
    SETTINGS = settings_get_defaults()
    
    # ----- Consoles + Player Ships -----
    
    all_consoles_script_info = gui_get_console_types()
    
    # Consoles
    
    # All the mast that defines consoles must execute before any console data
    # can initialize.
    # Ideally, ship-specific vs. ship-agnostic would probably be defined by
    # a simple boolean in the same line as the @console decorator label
    # (see `sbs_utils/mast_sbs/story_nodes/gui_console_decorator_label.py`).
    # But 1) that sounds complicated, and 2) it still wouldn't fix the fact 
    # that sometimes consoles' "if" statements depend on variables that are
    # initialized inside their mast files.
    # So I just added this hacky delay as a workaround instead.
    # Times out after ~2s.
    yield AWAIT(delay_app(0.25))
    is_console_ship_specific_undefined = True
    for quarter_seconds_until_timeout in range(8, 0, -1):
        is_console_ship_specific_undefined = False
        for console_identifier in all_consoles_script_info:
            if is_console_ship_specific(console_identifier) is None:
                is_console_ship_specific_undefined = True
                break
        if not is_console_ship_specific_undefined:
            break
        print(f"Game setup data initialization is waiting for all the mast files with console definitions to be run/initialized. Console '{console_identifier}' does not yet have it defined. {quarter_seconds_until_timeout*0.25}s until timeout.")
        yield AWAIT(delay_app(0.25))
    if is_console_ship_specific_undefined:
        consoles_with_ship_specific_undefined = [identifier for identifier in all_consoles_script_info if is_console_ship_specific(identifier) is None]
        print(f"ERROR: Couldn't properly tell whether the following consoles are ship-specific or ship-agnostic. Continuing as if they were ship-specific. {consoles_with_ship_specific_undefined}")
    
    # This list should already be sorted according to each console's weight
    all_enabled_console_identifiers = [console.path for console in gui_get_console_type_list()]
    
    ship_specific_consoles_info = []
    ship_agnostic_console_slots = []
    console_exclusivities = SETTINGS.get("CONSOLE_EXCLUSIVITIES")
    for console_identifier in all_enabled_console_identifiers:
        if console_identifier in console_exclusivities:
            is_exclusive = console_exclusivities[console_identifier]
        else:
            is_exclusive = False
        console_script_info = all_consoles_script_info[console_identifier]
        display_name = console_script_info["display_name"]
        description = console_script_info["label"].desc
        sorting_weight = console_script_info["label"].raw_weight
        
        is_ship_specific = is_console_ship_specific(console_identifier)
        if is_ship_specific is None or is_ship_specific:
            # Must create different instances for each player ship
            # Save the data needed to create them later
            console_info = ConsoleInfo(console_identifier, is_exclusive, display_name, description, sorting_weight)
            ship_specific_consoles_info.append(console_info)
        else:
            console_slot = ConsoleSlot(console_identifier, is_exclusive, display_name, description, sorting_weight, ship_number=None)
            ship_agnostic_console_slots.append(console_slot)
    
    # Disconnects are handled by _game_setup_data_on_client_disconnect
    
    # Player ships
    
    # ignoring PLAYER_CREATE_DEFAULT because I can't tell what it could be useful for
    player_ship_count = SETTINGS.get("PLAYER_COUNT")
    player_ships_settings = SETTINGS.get("PLAYER_LIST")
    player_ships = {}
    for i, player_ship_settings in enumerate(player_ships_settings):
        ship_number = i + 1 # since ship_number will be displayed to players
        name = player_ship_settings["name"]
        side = player_ship_settings["side"]
        ship_type_key = player_ship_settings["ship"]
        ship_specific_console_slots = [ConsoleSlot(info.identifier, info.is_exclusive, info.display_name, info.description, info.sorting_weight, ship_number) for info in ship_specific_consoles_info]
        player_ships[ship_number] = PlayerShipSetupData(ship_number, name, side, ship_type_key, ship_specific_console_slots)
    
    # ----- Map + Map Options -----
    
    difficulty = SETTINGS.get("DIFFICULTY")
    
    seed_value = SETTINGS.get("seed_value")
    
    map_identifier = SETTINGS.get("WORLD_SELECT")
    
    terrain_freq = EnvironmentalFrequency(terrain_to_value(SETTINGS.get("TERRAIN_SELECT")))
    lethal_terrain_freq = EnvironmentalFrequency(terrain_to_value(SETTINGS.get("LETHAL_SELECT")))
    friendly_ships_freq = EnvironmentalFrequency(terrain_to_value(SETTINGS.get("FRIENDLY_SELECT")))
    monsters_freq = EnvironmentalFrequency(terrain_to_value(SETTINGS.get("MONSTER_SELECT")))
    upgrades_freq = EnvironmentalFrequency(terrain_to_value(SETTINGS.get("UPGRADE_SELECT")))
    time_limit_in_minutes = SETTINGS.get("GAME_TIME_LIMIT", 0)
    war_time_delay_in_minutes = SETTINGS.get("WAR_TIME_DELAY", 0)
    environment_settings = EnvironmentSetupData(terrain_freq, lethal_terrain_freq, friendly_ships_freq, monsters_freq, upgrades_freq, time_limit_in_minutes, war_time_delay_in_minutes)
    
    _set_game_setup_data(GameSetupData(ship_agnostic_console_slots, player_ships, player_ship_count, difficulty, seed_value, map_identifier, environment_settings))
    
    yield AWAIT(delay_app(0.25))
    
    signal_emit(game_setup_data_initialized_signal_identifier())
    
    yield END()

class ConsoleInfo:
    def __init__(self, identifier, is_exclusive, display_name, description, sorting_weight):
        self.identifier = identifier
        self.is_exclusive = is_exclusive
        self.display_name = display_name
        self.description = description
        self.sorting_weight = sorting_weight

# ----- Main -----

def setup_game():
    SETTINGS = settings_get_defaults()
    GAME_SETUP_DATA = get_game_setup_data()
    VESSEL_TYPES_DATA = get_vessel_types_data()
    SHARED = get_shared_variable("SHARED")
    
    # Copied and adapted from server_console.mast
    
    # Player = 7 points of damage, npc = a range 3.5 - 8.5 
    sbs.set_beam_damages(0, _PLAYER_BEAM_DAMAGE_COEFF, (GAME_SETUP_DATA.difficulty / 2.0) + 3.0)
    
    # Create standard missile types
    sbs.set_shared_string("Homing","gui_text:Homing;  speed:10; lifetime:25; flare_color:white; trail_color:white;warhead:standard;damage:35; explosion_size:10;explosion_color:fire; behavior:homing; energy_conversion_value:100")
    sbs.set_shared_string("Nuke"  ,"gui_text:Nuke  ;  speed:10; lifetime:25; flare_color:white; trail_color:#99f;warhead:blast; blast_radius:1000; damage:5; explosion_size:20;explosion_color:fire; behavior:homing; energy_conversion_value:200")
    sbs.set_shared_string("EMP"   , "gui_text:EMP  ;  speed:10; lifetime:25; flare_color:yellow; trail_color:#99f;warhead:blast,reduce_shields; blast_radius:1000; damage:50; explosion_size:20;explosion_color:#11F; behavior:homing; energy_conversion_value:50")
    sbs.set_shared_string("Mine"  , "gui_text:Mine ;  speed:10; lifetime:25; flare_color:white; trail_color:white; warhead:blast; blast_radius:1000; damage:5; explosion_size:20; explosion_color:fire; behavior:mine; energy_conversion_value:200")
    
    time_limit_in_minutes = GAME_SETUP_DATA.environment_settings.time_limit_in_minutes
    if time_limit_in_minutes > 0:
        set_timer(SHARED, "time_limit", minutes=time_limit_in_minutes)
    
    extra_scan_sources_schedule()
    
    # Player ships
    for ship_number in range(1, GAME_SETUP_DATA.player_ship_count + 1):
        player_ship_setup_data = GAME_SETUP_DATA.get_player_ship_by_number(ship_number)
        player_ship_type = VESSEL_TYPES_DATA.get_ship_type_from_key(player_ship_setup_data.ship_type_key)
        
        # TODO don't hardcode the side
        player_ship_spawn_data = player_spawn(0, 0, 0, player_ship_setup_data.name, "tsn", player_ship_setup_data.ship_type_key)
        set_face(player_ship_spawn_data.id, random_face(player_ship_type.origin))
        set_inventory_value(player_ship_spawn_data.id, "respawn_time", 5)
        add_role(player_ship_spawn_data.id, "default_player_ship")
        
        # I have absolutely no clue why, but jump_drive_active needs to be set here,
        # while warp_drive_active and eng_control_label needs to be set in a //spawn
        # (grid_ai.mast). Otherwise, when the game starts and the helm/engineering
        # consoles were ready beforehand, then the helm console might enable the wrong
        # controls, and the engineering console might show the incorrect subsystem label.
        player_ship_blob = to_blob(player_ship_spawn_data.id)
        player_ship_blob.set("jump_drive_active", player_ship_type.has_jump_drive, 0)
        
        # I tried moving grid_rebuild_grid_objects here too. But for some reason,
        # that was causing the engineering grid widget to never get colored correctly
        # for the player ship. I checked if grid_get_grid_current_theme was returning
        # something bad, but it was returning the correct dictionary. I also tried a
        # task_schedule with a short delay, but that still ran into the same problems.
        # So I just gave up and left it where it was (in a //spawn in ai/grid_ai.mast).
        #grid_rebuild_grid_objects(player_ship_spawn_data.id, grid_get_grid_data())
        
        player_ship_setup_data.spawned_ship_id = player_ship_spawn_data.id
        
        signal_emit(signal_player_ship_created(), data={"PLAYER_SHIP_ID": player_ship_spawn_data.id})
    
    #sbs.assign_client_to_ship(0, GAME_SETUP_DATA.get_player_ship_by_number(1).spawned_ship_id)
    
    # TODO Is this necessary? (Do some custom mission scripts use it?)
    #signal_emit("create_player_ships", None)
    
    for map_obj in maps_get_list():
        if map_obj.path == GAME_SETUP_DATA.map_identifier:
            set_variable("WORLD_SELECT", map_obj)
            task_schedule(map_obj)
            break
    
    return

@label()
def _player_ship_spawn_actions_after_delay():
    player_ship_id = get_variable("PLAYER_SHIP_ID")
    yield AWAIT(delay_app(0.1))
    
    grid_rebuild_grid_objects(player_ship_id, grid_get_grid_data())
    
    yield END()

# ----- Misc -----

_PLAYER_BEAM_DAMAGE_COEFF = 7.0

# ----- Signal responses -----

@label()
def _game_setup_data_on_client_disconnect():
    client_id = get_variable("client_id")
    GAME_SETUP_DATA = get_game_setup_data()
    # check `not None` just in case this signal runs
    # prior to GAME_SETUP_DATA being initialized
    if GAME_SETUP_DATA is not None:
        GAME_SETUP_DATA.remove_client(client_id)
    yield END()

@label()
def _game_setup_data_before_player_ship_destroyed():
    DESTROYING_PLAYER_SHIP_ID = get_variable("DESTROYING_PLAYER_SHIP_ID")
    GAME_SETUP_DATA = get_game_setup_data()
    
    player_ship_setup_data = GAME_SETUP_DATA.get_player_ship_by_spawned_ship_id(DESTROYING_PLAYER_SHIP_ID)
    if player_ship_setup_data is not None:
        player_ship_setup_data.is_destroyed = True
        # Keep spawned_ship_id around until the ship is actually destroyed,
        # so that other before-destroy code can reference it
    
    yield END()

@label()
def _game_setup_data_after_player_ship_destroyed():
    DESTROYING_PLAYER_SHIP_ID = get_variable("DESTROYING_PLAYER_SHIP_ID")
    GAME_SETUP_DATA = get_game_setup_data()
    
    player_ship_setup_data = GAME_SETUP_DATA.get_player_ship_by_spawned_ship_id(DESTROYING_PLAYER_SHIP_ID)
    if player_ship_setup_data is not None:
        player_ship_setup_data.spawned_ship_id = None
    
    yield END()

@label()
def _game_setup_data_on_set_up_for_new():
    
    GAME_SETUP_DATA = get_game_setup_data()
    for player_ship_setup_data in GAME_SETUP_DATA.player_ships.values():
        player_ship_setup_data.is_destroyed = False
    
    yield END()

# ----- Setter/getter wrappers -----

# game setup data

def get_game_setup_data():
    return get_shared_variable(_GAME_SETUP_DATA_VAR_NAME)

def _set_game_setup_data(setup_data):
    set_shared_variable(_GAME_SETUP_DATA_VAR_NAME, setup_data)

_GAME_SETUP_DATA_VAR_NAME = "_game_setup_data"

# ship-specific and ship-agnostic consoles

def set_is_console_ship_specific(console_identifier, is_ship_specific):
    list_var_name = _SHIP_SPECIFIC_CONSOLES_VAR_NAME if is_ship_specific else _SHIP_AGNOSTIC_CONSOLES_VAR_NAME
    consoles = get_shared_variable(list_var_name)
    if consoles is None:
        consoles = []
    consoles.append(console_identifier)
    set_shared_variable(list_var_name, consoles)

def is_console_ship_specific(console_identifier):
    if console_identifier in get_shared_variable(_SHIP_SPECIFIC_CONSOLES_VAR_NAME):
        return True
    elif console_identifier in get_shared_variable(_SHIP_AGNOSTIC_CONSOLES_VAR_NAME):
        return False
    else:
        return None

def get_ship_specific_consoles():
    return get_shared_variable(_SHIP_SPECIFIC_CONSOLES_VAR_NAME)

def get_ship_agnostic_consoles():
    return get_shared_variable(_SHIP_AGNOSTIC_CONSOLES_VAR_NAME)

_SHIP_SPECIFIC_CONSOLES_VAR_NAME = "ship_specific_consoles"
_SHIP_AGNOSTIC_CONSOLES_VAR_NAME = "ship_agnostic_consoles"

# signals

def game_setup_data_initialized_signal_identifier():
    return "game_setup_data_initialized"

def signal_player_ship_created():
    return "player_ship_created"
