from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import END, get_variable, set_variable, set_shared_variable
from sbs_utils.procedural.gui import gui_button, gui_int_slider, gui_message
from sbs_utils.procedural.signal import signal_register

from data.missions.common.library_function_patches import gui_represent_patched
from data.missions.common.gui_color_scheme import color_text, color_text_secondary

from model_game_setup_data import signal_game_setup_data_player_ship_count_changed
from controller_game_setup_data import get_game_setup_data

# ----- creation -----

def create_player_ship_count_control():
    GAME_SETUP_DATA = get_game_setup_data()
    max_player_ship_count = GAME_SETUP_DATA.get_max_player_ship_count()
    
    decrease_button = gui_button("-", style=f"font:gui-3;col-width:30px;padding:0,3px;color:{color_text_secondary()};")
    slider = gui_int_slider(f"$text:int;low:1;high:{max_player_ship_count};", style=f"padding:0,3px;color:{color_text()}")
    slider.value = GAME_SETUP_DATA.player_ship_count
    increase_button = gui_button("+", style=f"font:gui-3;col-width:30px;padding:0,3px;color:{color_text_secondary()};")
    
    _set_player_ship_count_slider(slider)
    
    gui_message(decrease_button, _on_player_ship_count_decrease_clicked)
    gui_message(slider, _on_player_ship_count_slider_moved)
    gui_message(increase_button, _on_player_ship_count_increase_clicked)
    signal_register(signal_game_setup_data_player_ship_count_changed(), _player_ship_count_control_on_player_ship_count_changed, is_temporary=True)

@label()
def _on_player_ship_count_slider_moved():
    slider = _get_player_ship_count_slider()
    GAME_SETUP_DATA = get_game_setup_data()
    
    GAME_SETUP_DATA.player_ship_count = slider.value
    # See comment at the top of gui_game_setup.mast next to PLAYER_COUNT's definition
    set_shared_variable("PLAYER_COUNT", slider.value)
    
    yield END()

@label()
def _on_player_ship_count_decrease_clicked():
    GAME_SETUP_DATA = get_game_setup_data()
    
    # This will trigger _player_ship_count_control_on_player_ship_count_changed
    # which should sync everything else
    GAME_SETUP_DATA.player_ship_count -= 1
    
    yield END()

@label()
def _on_player_ship_count_increase_clicked():
    GAME_SETUP_DATA = get_game_setup_data()
    
    # This will trigger _player_ship_count_control_on_player_ship_count_changed
    # which should sync everything else
    GAME_SETUP_DATA.player_ship_count += 1
    
    yield END()

@label()
def _player_ship_count_control_on_player_ship_count_changed():
    slider = _get_player_ship_count_slider()
    GAME_SETUP_DATA = get_game_setup_data()
    
    if slider.value != GAME_SETUP_DATA.player_ship_count:
        slider.value = GAME_SETUP_DATA.player_ship_count
        gui_represent_patched(slider)
        # See comment at the top of gui_game_setup.mast next to PLAYER_COUNT's definition
        set_shared_variable("PLAYER_COUNT", GAME_SETUP_DATA.player_ship_count)
    
    yield END()

# ----- setter/getter wrappers -----

def _get_player_ship_count_slider():
    return get_variable(_PLAYER_SHIP_COUNT_SLIDER_VAR_NAME)

def _set_player_ship_count_slider(slider):
    set_variable(_PLAYER_SHIP_COUNT_SLIDER_VAR_NAME, slider)

_PLAYER_SHIP_COUNT_SLIDER_VAR_NAME = "_player_ship_count_slider"
