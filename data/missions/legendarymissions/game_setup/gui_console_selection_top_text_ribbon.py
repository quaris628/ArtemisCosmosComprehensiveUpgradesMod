"""
Creating and updating the gui text elements that appear in a ribbon
along the top of the console selection screen
"""

from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import END, get_variable, set_variable
from sbs_utils.procedural.signal import signal_register
from sbs_utils.procedural.gui import gui_section, gui_text

from data.missions.common.library_function_patches import gui_represent_patched
from data.missions.common.gui_color_scheme import color_text, color_background

from game_state import get_game_state, signal_game_state_changed, game_state_setting_up, game_state_running, game_state_paused, game_state_ended

def gui_create_top_text_ribbon(game_state):
    if game_state is None:
        game_state = get_game_state()
    
    gui_section(style=f"area:200px,0,100-30px,36px;background:{color_background()};")
    gui_text("")
    # I tried putting these two texts side-by-side in a single section,
    # but that caused the first to have an unnecessary line break
    gui_section(style="area:210px,8px,670px,36px;")
    # Artemis 2.8 text: "Choose your station(s) and press the 'Ready To Play' button."
    gui_text("Choose your console(s) then select 'Ready to Play'.", style=f"color:{color_text()}")
    gui_section(style="area:100-400px,5px,100-46px,36px;")
    simulation_status_text = gui_text(_get_simulation_status_display_text(game_state), style=f"justify:right;font:gui-3;color:{color_text()};")
    
    set_variable(_SIMULATION_STATUS_TEXT_VAR_NAME, simulation_status_text)
    signal_register(signal_game_state_changed(), _update_simulation_status_text, is_temporary=True)

@label()
def _update_simulation_status_text():
    game_state = get_game_state()
    simulation_status_text = get_variable(_SIMULATION_STATUS_TEXT_VAR_NAME)
    simulation_status_text.value = _get_simulation_status_display_text(game_state)
    gui_represent_patched(simulation_status_text)
    yield END()

def _get_simulation_status_display_text(game_state):
    if game_state == game_state_setting_up():
        return "Simulation is not running"
    elif game_state == game_state_running():
        return "Simulation is running"
    elif game_state == game_state_paused():
        return "Simulation is paused"
    elif game_state == game_state_ended():
        return "Simulation is not running"
    else:
        return "Simulation status unclear"

_SIMULATION_STATUS_TEXT_VAR_NAME = "_gui_console_selection_simulation_status_text"
