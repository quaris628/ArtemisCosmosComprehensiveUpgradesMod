
from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import AWAIT, END, get_variable, set_variable, task_schedule
from sbs_utils.procedural.signal import signal_register
from sbs_utils.procedural.gui import gui_blank, gui_button, gui_message, gui_hide, gui_section, gui_show, gui_text
from sbs_utils.procedural.timers import delay_app

from data.missions.common.library_function_patches import gui_represent_patched, gui_dropdown_patched
from data.missions.common.controller_vessel_types_data import get_vessel_types_data
from data.missions.common.gui_color_scheme import color_text, color_text_secondary

from model_player_ship_setup_data import signal_player_ship_setup_data_ship_type_changed
from model_game_setup_data import signal_game_setup_data_player_ship_availability_changed
from controller_game_setup_data import get_game_setup_data
from game_state import is_game_in_progress

# ----- creation -----

def create_player_ship_type_controls(ship, use_large_next_prev_buttons=False, next_prev_x_left=None, next_prev_y_top=None, next_prev_x_right=None):
    VESSEL_TYPES_DATA = get_vessel_types_data()
    ship_type = VESSEL_TYPES_DATA.get_ship_type_from_key(ship.ship_type_key)
    
    if not use_large_next_prev_buttons:
        previous_button = gui_button("<", data={"SHIP": ship}, style=f"font:gui-3;col-width:28px;padding:0,0,5px,0;color:{color_text_secondary()};")
    ship_origin_dropdown = gui_dropdown_patched(VESSEL_TYPES_DATA.get_all_origins_csv(), value=ship_type.origin, style=f"font:gui-3;col-width:190px;color:{color_text()};", data={"SHIP": ship})
    if not use_large_next_prev_buttons:
        gui_blank(style="col-width:5px;")
    else:
        gui_blank(style="col-width:10px;")
    ship_type_name_dropdown = gui_dropdown_patched(VESSEL_TYPES_DATA.get_ship_type_name_csvs_for_origin(ship_type.origin), value=ship_type.ship_type_name, style=f"font:gui-3;col-width:295px;color:{color_text()};", data={"SHIP": ship})
    if not use_large_next_prev_buttons:
        next_button = gui_button(">", data={"SHIP": ship}, style=f"font:gui-3;col-width:28px;padding:5px,0;color:{color_text_secondary()};")
    else: # large next/prev buttons
        next_prev_y_bottom = f"{next_prev_y_top}+30px"
        gui_section(style=f"area:{next_prev_x_left},{next_prev_y_top},{next_prev_x_right},{next_prev_y_bottom};")
        previous_button = gui_button("", data={"SHIP": ship})
        gui_blank(style="col-width:10px;")
        next_button = gui_button("", data={"SHIP": ship})
        gui_section(style=f"area:{next_prev_x_left},{next_prev_y_top},{next_prev_x_right},{next_prev_y_bottom};")
        gui_text("< Previous", style=f"font:gui-3;padding:10px,2px;justify:left;color:{color_text_secondary()};")
        gui_text("Next >", style=f"font:gui-3;padding:0,2px,10px,0;justify:right;color:{color_text_secondary()};")
    
    # previous_button will always be assigned, but pylint thinks it might not be
    _set_ship_type_dropdowns(ship.number, ship_origin_dropdown, ship_type_name_dropdown, next_button, previous_button) # pylint: disable=possibly-used-before-assignment
    
    gui_message(ship_origin_dropdown, _player_ship_type_controls_on_origin_dropdown_changed)
    gui_message(ship_type_name_dropdown, _player_ship_type_controls_on_ship_type_name_dropdown_changed)
    gui_message(previous_button, _player_ship_type_controls_on_previous_button_clicked)
    gui_message(next_button, _player_ship_type_controls_on_next_button_clicked)
    signal_register(signal_player_ship_setup_data_ship_type_changed(ship.number), _player_ship_type_controls_on_ship_type_changed, is_temporary=True)
    signal_register(signal_game_setup_data_player_ship_availability_changed(ship.number), _player_ship_type_controls_on_availability_changed, is_temporary=True)
    
    task_schedule(_player_ship_type_controls_update_after_delay, data={"SHIP": ship})

@label()
def _player_ship_type_controls_update_after_delay():
    GAME_SETUP_DATA = get_game_setup_data()
    ship = get_variable("SHIP")
    ship_origin_dropdown, ship_type_name_dropdown, next_button, previous_button = _get_ship_type_dropdowns(ship.number)
    
    # If an element is hidden prior to it being presented for the first time,
    # then it will never show again.
    # https://github.com/artemis-sbs/LegendaryMissions/issues/513#issuecomment-3931007180
    # So work around this by adding a short delay before hiding the element,
    # so that the element will (hopefully) have been presented already by the
    # time gui_hide is called.
    yield AWAIT(delay_app(0))
    
    if GAME_SETUP_DATA.player_ship_count < ship.number:
        gui_hide(ship_origin_dropdown)
        gui_hide(ship_type_name_dropdown)
        gui_hide(next_button)
        gui_hide(previous_button)
    gui_represent_patched(ship_origin_dropdown)
    gui_represent_patched(ship_type_name_dropdown)
    gui_represent_patched(next_button)
    gui_represent_patched(previous_button)
    
    yield END()

# ----- syncing -----

@label()
def _player_ship_type_controls_on_origin_dropdown_changed():
    if is_game_in_progress():
        yield END()
    VESSEL_TYPES_DATA = get_vessel_types_data()
    ship = get_variable("SHIP")
    ship_type = VESSEL_TYPES_DATA.get_ship_type_from_key(ship.ship_type_key)
    ship_origin_dropdown, ship_type_name_dropdown, next_button, previous_button = _get_ship_type_dropdowns(ship.number)
    
    if ship_type.origin != ship_origin_dropdown.value:
        new_ship_type = VESSEL_TYPES_DATA.get_first_ship_type_of_origin(ship_origin_dropdown.value)
        # Setting this will trigger _player_ship_type_controls_on_ship_type_changed
        ship.ship_type_key = new_ship_type.ship_type_key
    
    yield END()

@label()
def _player_ship_type_controls_on_ship_type_name_dropdown_changed():
    if is_game_in_progress():
        yield END()
    VESSEL_TYPES_DATA = get_vessel_types_data()
    ship = get_variable("SHIP")
    ship_type = VESSEL_TYPES_DATA.get_ship_type_from_key(ship.ship_type_key)
    ship_origin_dropdown, ship_type_name_dropdown, next_button, previous_button = _get_ship_type_dropdowns(ship.number)
    
    if ship_type.ship_type_name != ship_type_name_dropdown.value:
        new_ship_type = VESSEL_TYPES_DATA.get_ship_type_from_origin_and_name(ship_origin_dropdown.value, ship_type_name_dropdown.value)
        # Setting this will trigger _player_ship_type_controls_on_ship_type_changed
        ship.ship_type_key = new_ship_type.ship_type_key
    
    yield END()

@label()
def _player_ship_type_controls_on_ship_type_changed():
    VESSEL_TYPES_DATA = get_vessel_types_data()
    ship = get_variable("SHIP")
    ship_type = VESSEL_TYPES_DATA.get_ship_type_from_key(ship.ship_type_key)
    ship_origin_dropdown, ship_type_name_dropdown, next_button, previous_button = _get_ship_type_dropdowns(ship.number)
    
    if ship_origin_dropdown.value != ship_type.origin:
        ship_origin_dropdown.value = ship_type.origin
        gui_represent_patched(ship_origin_dropdown)
    
    # It is possible that just the origin is different
    # and the ship type name is the same.
    # For example:
    # Arvonian/Terran/Ximni Carrier, Light Carrier, and Destroyer;
    # Terran/Ximni Light Cruiser, Scout, Escort, Dreadnought, etc.
    #
    # But if so, we still need to update the ship type name dropdown
    # so that its list of options matches the new origin.
    #
    # Also, the ship type might have changed because of a change
    # to the origin dropdown (meaning the dropdown wouldn't be dirty),
    # and we need to update the ship type name dropdown's list of
    # in this case.
    #
    # To simplify all this, always update the ship type name dropdown.
    # (In the unlikely event that this makes performance noticeably bad,
    # maybe cull the unnecessary updates when neither the origin nor
    # ship type name dropdowns are dirty and the update wasn't initiated
    # by a click changing the origin dropdown.)
    
    ship_type_name_dropdown.values_as_csv = VESSEL_TYPES_DATA.get_ship_type_name_csvs_for_origin(ship_type.origin)
    ship_type_name_dropdown.value = ship_type.ship_type_name
    gui_represent_patched(ship_type_name_dropdown)
    
    yield END()

@label()
def _player_ship_type_controls_on_previous_button_clicked():
    if is_game_in_progress():
        yield END()
    VESSEL_TYPES_DATA = get_vessel_types_data()
    ship = get_variable("SHIP")
    
    ship.ship_type_key = VESSEL_TYPES_DATA.get_ship_type_key_before(ship.ship_type_key).ship_type_key
    
    yield END()

@label()
def _player_ship_type_controls_on_next_button_clicked():
    if is_game_in_progress():
        yield END()
    VESSEL_TYPES_DATA = get_vessel_types_data()
    ship = get_variable("SHIP")
    
    ship.ship_type_key = VESSEL_TYPES_DATA.get_ship_type_key_after(ship.ship_type_key).ship_type_key
    
    yield END()

@label()
def _player_ship_type_controls_on_availability_changed():
    ship = get_variable("SHIP")
    is_available = get_variable("IS_AVAILABLE")
    ship_origin_dropdown, ship_type_name_dropdown, next_button, previous_button = _get_ship_type_dropdowns(ship.number)
    
    if is_available:
        gui_show(ship_origin_dropdown)
        gui_show(ship_type_name_dropdown)
        gui_show(next_button)
        gui_show(previous_button)
    else:
        gui_hide(ship_origin_dropdown)
        gui_hide(ship_type_name_dropdown)
        gui_hide(next_button)
        gui_hide(previous_button)
    gui_represent_patched(ship_origin_dropdown)
    gui_represent_patched(ship_type_name_dropdown)
    gui_represent_patched(next_button)
    gui_represent_patched(previous_button)
    
    yield END()

# ----- setter/getter wrappers -----

def _get_ship_type_dropdowns(ship_number):
    ship_type_dropdowns = get_variable(_SHIP_TYPE_DROPDOWNS_VAR_NAME)
    elements = ship_type_dropdowns[ship_number]
    return elements[0], elements[1], elements[2], elements[3]

def _set_ship_type_dropdowns(ship_number, ship_origin_dropdown, ship_type_name_dropdown, next_button, previous_button):
    ship_type_dropdowns = get_variable(_SHIP_TYPE_DROPDOWNS_VAR_NAME)
    if ship_type_dropdowns is None:
        ship_type_dropdowns = {}
    ship_type_dropdowns[ship_number] = (ship_origin_dropdown, ship_type_name_dropdown, next_button, previous_button)
    set_variable(_SHIP_TYPE_DROPDOWNS_VAR_NAME, ship_type_dropdowns)

_SHIP_TYPE_DROPDOWNS_VAR_NAME = "_ship_type_dropdowns"
