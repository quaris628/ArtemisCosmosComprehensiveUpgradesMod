
from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import END, get_variable, set_variable
from sbs_utils.procedural.signal import signal_register
from sbs_utils.procedural.gui import gui_section, gui_text, gui_message, gui_ship

from data.missions.common.library_function_patches import gui_represent_patched, gui_dropdown_patched
from data.missions.common.gui_color_scheme import color_text, color_text_secondary
from data.missions.common.controller_vessel_types_data import get_vessel_types_data

from model_player_ship_setup_data import signal_player_ship_setup_data_ship_type_changed
from controller_game_setup_data import get_game_setup_data

# ----- creation -----

def create_3d_ship_display(ship, x_left, y_top, x_right, y_bottom):
    
    gui_section(style=f"area:{x_left},{y_top},{x_right},{y_bottom};")
    threeD_ship_display = gui_ship(ship.ship_type_key)
    
    _set_3d_ship_display(threeD_ship_display)
    
    signal_register(signal_player_ship_setup_data_ship_type_changed(ship.number), _sync_3d_ship_display_on_ship_type_changed, is_temporary=True)

# ----- syncing -----

@label()
def _sync_3d_ship_display_on_ship_type_changed():
    ship = get_variable("SHIP")
    threeD_ship_display = _get_3d_ship_display()
    
    # Reading threeD_ship_display.value or .ship causes a crash
    # https://github.com/artemis-sbs/LegendaryMissions/issues/585
    if threeD_ship_display._ship[:8] != ship.ship_type_key:
        threeD_ship_display.value = ship.ship_type_key
        gui_represent_patched(threeD_ship_display)
    
    yield END()

# ----- setter/getter wrappers -----

def _get_3d_ship_display():
    return get_variable(_3D_SHIP_DISPLAY_VAR_NAME)

def _set_3d_ship_display(threeD_ship_display):
    set_variable(_3D_SHIP_DISPLAY_VAR_NAME, threeD_ship_display)

_3D_SHIP_DISPLAY_VAR_NAME = "_3d_ship_display"
