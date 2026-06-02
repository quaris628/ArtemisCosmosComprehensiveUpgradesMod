"""
Customize ship button in console selection
"""

from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import END, get_variable, set_variable, task_schedule, AWAIT
from sbs_utils.procedural.signal import signal_register
from sbs_utils.procedural.gui import gui_section, gui_text, gui_button, gui_message, gui_show, gui_hide
from sbs_utils.procedural.timers import delay_app

from data.missions.common.library_function_patches import gui_represent_patched
from data.missions.common.gui_color_scheme import color_text
from data.missions.common.operator_mode import is_client_verified_operator_admin, is_editing_player_ships_disabled

from model_console_slot import signal_console_slot_deselect_or_select
from controller_game_setup_data import get_game_setup_data
from game_state import is_game_in_progress, signal_game_started, signal_game_ended
from gui_customize_ship import gui_switch_to_customize_ship

# ----- creation -----

def gui_create_customize_ship_button(client_id, x_left, y_top, x_right, y_bottom):
    
    if not is_client_verified_operator_admin() and is_editing_player_ships_disabled():
        return
    
    gui_section(style=f"area:{x_left},{y_top},{x_right},{y_bottom};")
    button = gui_button("")
    
    # Use separate text element for the label, so that the text can be centered
    gui_section(style=f"area:{x_left},{y_top},{x_right},{y_bottom};")
    button_label = gui_text("Customize Ship", style=f"font:gui-3;justify:center;color:{color_text()};")
    
    _set_customize_ship_gui_elements(button, button_label)
    
    gui_message(button, _on_customize_ship_button_clicked)
    signal_register(signal_console_slot_deselect_or_select(client_id), _sync_customize_ship_button_on_console_selection_changed, is_temporary=True)
    signal_register(signal_game_started(), _sync_customize_ship_button_on_game_started, is_temporary=True)
    signal_register(signal_game_ended(), _sync_customize_ship_button_on_game_ended, is_temporary=True)
    
    task_schedule(_update_customize_ship_button_after_delay)

@label()
def _update_customize_ship_button_after_delay():
    # If an element is hidden prior to it being presented for the first time,
    # then it will never show again.
    # https://github.com/artemis-sbs/LegendaryMissions/issues/513#issuecomment-3931007180
    # So work around this by adding a short delay before hiding the element,
    # so that the element will (hopefully) have been presented already by the
    # time gui_hide is called.
    yield AWAIT(delay_app(0))
    client_id = get_variable("client_id")
    
    _sync_showing_or_hiding_customize_ship_button(client_id)
    
    yield END()

# ----- on-events/syncing -----

@label()
def _on_customize_ship_button_clicked():
    GAME_SETUP_DATA = get_game_setup_data()
    client_id = get_variable("client_id")
    
    GAME_SETUP_DATA.client_unready(client_id)
    gui_switch_to_customize_ship(GAME_SETUP_DATA.get_selected_ship(client_id), back_label="gui_console_selection_main", delay_reroute_workaround=True)
    
    yield END()

@label()
def _sync_customize_ship_button_on_console_selection_changed():
    client_id = get_variable("client_id")
    
    _sync_showing_or_hiding_customize_ship_button(client_id)
    
    yield END()

@label()
def _sync_customize_ship_button_on_game_started():
    
    # TODO allow viewing, but not editing, after game has started
    
    button, button_label = _get_customize_ship_gui_elements()
    gui_hide(button)
    gui_hide(button_label)
    gui_represent_patched(button)
    gui_represent_patched(button_label)
    
    yield END()

@label()
def _sync_customize_ship_button_on_game_ended():
    client_id = get_variable("client_id")
    
    _sync_showing_or_hiding_customize_ship_button(client_id)
    
    yield END()

def _sync_showing_or_hiding_customize_ship_button(client_id):
    button, button_label = _get_customize_ship_gui_elements()
    show = _can_customize_ship(client_id) and not is_game_in_progress()
    if show != button.is_hidden:
        return
    if show and button.is_hidden:
        gui_show(button)
        gui_show(button_label)
    else:
        gui_hide(button)
        gui_hide(button_label)
    gui_represent_patched(button)
    gui_represent_patched(button_label)

# ----- misc -----

def _console_identifiers_that_give_customize_ship_perms():
    return ["helm", "mainscreen"]

def _can_customize_ship(client_id):
    GAME_SETUP_DATA = get_game_setup_data()
    selected_ship = GAME_SETUP_DATA.get_selected_ship(client_id)
    if selected_ship is None:
        return False
    for console_identifier in _console_identifiers_that_give_customize_ship_perms():
        console_slot = selected_ship.get_console_slot(console_identifier)
        if console_slot is None:
            continue
        if console_slot.is_selected_by_client(client_id):
            return True
    return False

# ----- setter/getter wrappers -----

def _get_customize_ship_gui_elements():
    elements = get_variable(_CUSTOMIZE_SHIP_BUTTON_GUI_ELEMENTS_VAR_NAME)
    return elements[0], elements[1]

def _set_customize_ship_gui_elements(button, button_label):
    set_variable(_CUSTOMIZE_SHIP_BUTTON_GUI_ELEMENTS_VAR_NAME, (button, button_label))

_CUSTOMIZE_SHIP_BUTTON_GUI_ELEMENTS_VAR_NAME = "_gui_console_selection_customize_ship_button_gui_elements"

# ----- signals -----

def signal_console_selection_customize_ship_button_clicked(client_id):
    return f"cs_customize_ship_button_clicked_{client_id}"
