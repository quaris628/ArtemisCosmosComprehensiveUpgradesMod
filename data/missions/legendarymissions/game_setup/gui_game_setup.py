import sbs

from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import AWAIT, END, get_variable, set_variable
from sbs_utils.procedural.gui import gui_hide, gui_row, gui_text, gui_show
from sbs_utils.procedural.maps import map_get_properties
from sbs_utils.procedural.timers import delay_app

from data.missions.common.library_function_patches import gui_represent_patched
from data.missions.common.gui_top_tabs import gui_create_top_tabs, GuiTopTab

from controller_game_setup_data import get_game_setup_data

# ----- top tabs -----

def gui_game_setup_create_top_tabs(current_tab_key):
    gui_create_top_tabs(current_tab_key, get_gui_game_setup_top_tabs(), x_left_px=300, y_top_px=42, force_show_all_text=True)

def get_gui_game_setup_top_tabs():
    return [
        GuiTopTab(gui_top_tab_scenario_key(), "Scenario", "gui_game_setup_scenario_tab"),
        GuiTopTab(gui_top_tab_player_ships_key(), "Player Ships", "gui_game_setup_player_ships_tab"),
        # TODO re-enable connections tab when it's fleshed out
        #GuiTopTab(gui_top_tab_connections_key(), "Connections", "gui_game_setup_connections_tab")
    ]

def gui_top_tab_scenario_key():
    return "scenario"

def gui_top_tab_player_ships_key():
    return "player_ships"

def gui_top_tab_connections_key():
    return "connections"

# ----- map picker -----

def get_map_properties_with_demo_check(map_identifier):
    # Demo only has DIFFICULTY
    # (Maybe this demo check should just be moved into
    # the map_get_properties() function in sbs_utils)
    if sbs.is_demo():
        
        return "\nMain:\n    Difficulty: 'gui_int_slider(\"$text:int;low: 1.0;high:11.0\", var=\"DIFFICULTY\")'\n"
    return map_get_properties(map_identifier)

def map_listbox_template(map_object):
    gui_row("row-height:2px;background:#ddd;padding:10px,0,10px,3px;")
    gui_row("row-height:3em;padding:10px,10px,10px,3px;")
    gui_text(f"$text:{map_object.display_name};justify:left;font:gui-3;")
    gui_row("padding:10px,10px,10px,3px;")
    gui_text(f"$text:{map_object.desc};justify:left;color:#eee;font:gui-2;")

def map_listbox_title_template():
    gui_row("row-height:1.2em;padding:13px;background:#1578;")
    gui_text("$text:Mission Types;justify:left;")

# ----- player ships -----

@label()
def _gui_game_setup_player_ships_tab_update_after_delay():
    GAME_SETUP_DATA = get_game_setup_data()
    
    # If an element is hidden prior to it being presented for the first time,
    # then it will never show again.
    # https://github.com/artemis-sbs/LegendaryMissions/issues/513#issuecomment-3931007180
    # So work around this by adding a short delay before hiding the element,
    # so that the element will (hopefully) have been presented already by the
    # time gui_hide is called.
    yield AWAIT(delay_app(0))
    
    for ship in GAME_SETUP_DATA.player_ships.values():
        number_text, details_button = _get_player_ship_misc_gui_elements(ship.number)
        if GAME_SETUP_DATA.player_ship_count < ship.number:
            gui_hide(number_text)
            gui_hide(details_button)
        gui_represent_patched(number_text)
        gui_represent_patched(details_button)
    
    yield END()

@label()
def _gui_game_setup_player_ships_tab_on_availability_changed():
    ship = get_variable("SHIP")
    is_available = get_variable("IS_AVAILABLE")
    number_text, details_button = _get_player_ship_misc_gui_elements(ship.number)
    
    if is_available:
        gui_show(number_text)
        gui_show(details_button)
    else:
        gui_hide(number_text)
        gui_hide(details_button)
    gui_represent_patched(number_text)
    gui_represent_patched(details_button)
    
    yield END()

# ----- setter/getter wrappers -----

def _get_player_ship_misc_gui_elements(ship_number):
    elements = get_variable(_MISC_GUI_ELEMENTS_VAR_NAME)[ship_number]
    return elements[0], elements[1]

def _set_player_ship_misc_gui_elements(ship_number, number_text, details_button):
    misc_gui_elements = get_variable(_MISC_GUI_ELEMENTS_VAR_NAME)
    if misc_gui_elements is None:
        misc_gui_elements = {}
    misc_gui_elements[ship_number] = (number_text, details_button)
    set_variable(_MISC_GUI_ELEMENTS_VAR_NAME, misc_gui_elements)

_MISC_GUI_ELEMENTS_VAR_NAME = "_misc_gui_elements"
