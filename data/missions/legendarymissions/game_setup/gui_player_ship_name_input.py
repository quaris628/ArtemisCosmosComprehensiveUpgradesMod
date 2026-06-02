
from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import AWAIT, END, get_variable, set_variable, task_schedule
from sbs_utils.procedural.signal import signal_register
from sbs_utils.procedural.gui import gui_hide, gui_show, gui_message
from sbs_utils.procedural.timers import delay_app

from data.missions.common.library_function_patches import gui_represent_patched, gui_input
from data.missions.common.gui_color_scheme import color_text

from model_player_ship_setup_data import signal_player_ship_setup_data_name_changed
from model_game_setup_data import signal_game_setup_data_player_ship_availability_changed
from controller_game_setup_data import get_game_setup_data
from game_state import is_game_in_progress

# ----- creation -----

def create_ship_name_input(ship):
    # $text: format is necessary; if passing the raw ship name instead, then the
    # text box always contains the '`' character instead of the ship name for some reason.
    text_input = gui_input(f"$text:{ship.name};", style=f"font:gui-3;color:{color_text()};", data={"SHIP": ship})
    
    _set_customize_ship_text_input(ship.number, text_input)
    
    gui_message(text_input, _on_ship_name_text_input_typed_in)
    signal_register(signal_player_ship_setup_data_name_changed(ship.number), _sync_ship_name_text_input_on_ship_name_changed, is_temporary=True)
    signal_register(signal_game_setup_data_player_ship_availability_changed(ship.number), _player_ship_name_input_on_availability_changed, is_temporary=True)
    
    task_schedule(_player_ship_name_input_update_after_delay, data={"SHIP": ship})

@label()
def _player_ship_name_input_update_after_delay():
    GAME_SETUP_DATA = get_game_setup_data()
    ship = get_variable("SHIP")
    text_input = _get_customize_ship_text_input(ship.number)
    
    # If an element is hidden prior to it being presented for the first time,
    # then it will never show again.
    # https://github.com/artemis-sbs/LegendaryMissions/issues/513#issuecomment-3931007180
    # So work around this by adding a short delay before hiding the element,
    # so that the element will (hopefully) have been presented already by the
    # time gui_hide is called.
    yield AWAIT(delay_app(0))
    
    if GAME_SETUP_DATA.player_ship_count < ship.number:
        gui_hide(text_input)
    gui_represent_patched(text_input)
    
    yield END()

# ----- syncing -----

@label()
def _on_ship_name_text_input_typed_in():
    if is_game_in_progress():
        yield END()
    ship = get_variable("SHIP")
    text_input = _get_customize_ship_text_input(ship.number)
    
    if ship.name != text_input.value:
        # TODO maybe sanitize this name,
        # if there is no engine-level or sbs_utils-level sanitization added
        # https://github.com/artemis-sbs/LegendaryMissions/issues/569
        ship.name = text_input.value
    
    yield END()

@label()
def _sync_ship_name_text_input_on_ship_name_changed():
    ship = get_variable("SHIP")
    text_input = _get_customize_ship_text_input(ship.number)
    
    if text_input.value != ship.name:
        text_input.value = ship.name
        gui_represent_patched(text_input)
    
    yield END()

@label()
def _player_ship_name_input_on_availability_changed():
    ship = get_variable("SHIP")
    is_available = get_variable("IS_AVAILABLE")
    text_input = _get_customize_ship_text_input(ship.number)
    
    if is_available:
        gui_show(text_input)
    else:
        gui_hide(text_input)
    gui_represent_patched(text_input)
    
    yield END()

# ----- misc -----

def _set_customize_ship_text_input(ship_number, text_input):
    set_variable(_get_customize_ship_text_input_var_name(ship_number), text_input)

def _get_customize_ship_text_input(ship_number):
    return get_variable(_get_customize_ship_text_input_var_name(ship_number))

def _get_customize_ship_text_input_var_name(ship_number):
    return f"_customize_ship_text_input_{ship_number}"
