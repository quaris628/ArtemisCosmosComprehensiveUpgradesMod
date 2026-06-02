
from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import AWAIT, END, get_variable, set_variable, task_schedule
from sbs_utils.procedural.signal import signal_register
from sbs_utils.procedural.gui import gui_hide, gui_show, gui_text
from sbs_utils.procedural.timers import delay_app

from data.missions.common.library_function_patches import gui_represent_patched
from data.missions.common.controller_vessel_types_data import get_vessel_types_data
from data.missions.common.gui_color_scheme import color_text_secondary

from model_player_ship_setup_data import signal_player_ship_setup_data_ship_type_changed
from model_game_setup_data import signal_game_setup_data_player_ship_availability_changed
from controller_game_setup_data import get_game_setup_data

def create_player_ship_type_short_description_text(ship, style=None):
    if style is None:
        style = f"font:gui-1;color:{color_text_secondary()};"
    
    # Wait to populate text so it doesn't show before hiding
    description_text = gui_text("", style=style)
    
    _set_player_ship_type_short_description_text(ship.number, description_text)
    
    signal_register(signal_player_ship_setup_data_ship_type_changed(ship.number), _player_ship_type_short_description_on_ship_type_changed, is_temporary=True)
    signal_register(signal_game_setup_data_player_ship_availability_changed(ship.number), _player_ship_type_short_description_on_availability_changed, is_temporary=True)
    
    task_schedule(_player_ship_type_short_description_update_after_delay, data={"SHIP": ship, "DESCRIPTION_TEXT": description_text})

@label()
def _player_ship_type_short_description_update_after_delay():
    VESSEL_TYPES_DATA = get_vessel_types_data()
    GAME_SETUP_DATA = get_game_setup_data()
    ship = get_variable("SHIP")
    ship_type = VESSEL_TYPES_DATA.get_ship_type_from_key(ship.ship_type_key)
    description_text = _get_player_ship_type_short_description_text(ship.number)
    
    # If an element is hidden prior to it being presented for the first time,
    # then it will never show again.
    # https://github.com/artemis-sbs/LegendaryMissions/issues/513#issuecomment-3931007180
    # So work around this by adding a short delay before hiding the element,
    # so that the element will (hopefully) have been presented already by the
    # time gui_hide is called.
    yield AWAIT(delay_app(0))
    
    description_text.value = ship_type.get_short_description()
    if GAME_SETUP_DATA.player_ship_count < ship.number:
        gui_hide(description_text)
    gui_represent_patched(description_text)
    
    yield END()

@label()
def _player_ship_type_short_description_on_ship_type_changed():
    VESSEL_TYPES_DATA = get_vessel_types_data()
    ship = get_variable("SHIP")
    ship_type = VESSEL_TYPES_DATA.get_ship_type_from_key(ship.ship_type_key)
    description_text = _get_player_ship_type_short_description_text(ship.number)
    
    description_text.value = ship_type.get_short_description()
    gui_represent_patched(description_text)
    
    yield END()

@label()
def _player_ship_type_short_description_on_availability_changed():
    ship = get_variable("SHIP")
    is_available = get_variable("IS_AVAILABLE")
    description_text = _get_player_ship_type_short_description_text(ship.number)
    
    if is_available:
        gui_show(description_text)
    else:
        gui_hide(description_text)
    gui_represent_patched(description_text)
    
    yield END()

# ----- setter/getter wrappers -----

def _get_player_ship_type_short_description_text(ship_number):
    description_texts = get_variable(_PLAYER_SHIP_TYPE_SHORT_DESCRIPTION_TEXTS_VAR_NAME)
    return description_texts[ship_number]

def _set_player_ship_type_short_description_text(ship_number, description_text):
    description_texts = get_variable(_PLAYER_SHIP_TYPE_SHORT_DESCRIPTION_TEXTS_VAR_NAME)
    if description_texts is None:
        description_texts = {}
    description_texts[ship_number] = description_text
    set_variable(_PLAYER_SHIP_TYPE_SHORT_DESCRIPTION_TEXTS_VAR_NAME, description_texts)

_PLAYER_SHIP_TYPE_SHORT_DESCRIPTION_TEXTS_VAR_NAME = "player_ship_type_short_description_texts"
