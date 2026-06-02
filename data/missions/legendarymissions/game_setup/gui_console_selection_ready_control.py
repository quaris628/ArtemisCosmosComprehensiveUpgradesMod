"""
Creating and updating/syncing the checkboxes for player ships in console selection
"""

from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import AWAIT, END, get_variable, set_variable, task_schedule
from sbs_utils.procedural.signal import signal_register
from sbs_utils.procedural.gui import gui_checkbox, gui_hide, gui_message, gui_section, gui_show, gui_text
from sbs_utils.procedural.timers import delay_app

from data.missions.common.library_function_patches import gui_represent_patched
from data.missions.common.gui_color_scheme import color_text

from model_game_setup_data import signal_game_setup_data_client_ready_changed, signal_game_setup_data_can_client_ready_changed, signal_game_setup_data_can_client_enter_game_changed
from controller_game_setup_data import get_game_setup_data

# ----- creation -----

def create_ready_control(client_id, x_left, y_top, y_mid, x_right, y_bottom):
    GAME_SETUP_DATA = get_game_setup_data()
    
    gui_section(style=f"area:{x_left},{y_top},{x_right},{y_mid};")
    # Delay setting the actual string of text to display,
    # to avoid it showing for a moment before the element gets hidden
    cannot_enter_game_text = gui_text("Cannot Enter Game - Ship Destroyed!", style="font:gui-2;justify:center;padding:0,0,4px,0;color:#f44;background:#0004;")
    
    gui_section(style=f"area:{x_left},{y_mid},{x_right},{y_bottom};")
    checkbox = gui_checkbox("", style=f"color:{color_text()};")
    # might already be ready if a game just ended and another is being set up
    checkbox.value = GAME_SETUP_DATA.is_client_ready(client_id)
    
    # Use separate text element for the label, so that the text can be centered
    gui_section(style=f"area:{x_left},{y_mid},{x_right},{y_bottom};")
    checkbox_label = gui_text("Ready to Play", style=f"font:gui-3;justify:center;color:{color_text()};")
    
    _set_ready_control_gui_elements(checkbox, checkbox_label, cannot_enter_game_text)
    
    gui_message(checkbox, _on_ready_checkbox_clicked)
    signal_register(signal_game_setup_data_client_ready_changed(client_id), _sync_ready_checkbox_on_client_ready_changed, is_temporary=True)
    signal_register(signal_game_setup_data_can_client_ready_changed(client_id), _sync_ready_checkbox_on_can_client_ready_changed, is_temporary=True)
    signal_register(signal_game_setup_data_can_client_enter_game_changed(client_id), _sync_ready_checkbox_on_can_client_enter_game_changed, is_temporary=True)
    
    task_schedule(_update_ready_control_after_delay)

@label()
def _update_ready_control_after_delay():
    # If an element is hidden prior to it being presented for the first time,
    # then it will never show again.
    # https://github.com/artemis-sbs/LegendaryMissions/issues/513#issuecomment-3931007180
    # So work around this by adding a short delay before hiding the element,
    # so that the element will (hopefully) have been presented already by the
    # time gui_hide is called.
    yield AWAIT(delay_app(0))
    
    client_id = get_variable("client_id")
    GAME_SETUP_DATA = get_game_setup_data()
    checkbox, checkbox_label, cannot_enter_game_text = _get_ready_control_gui_elements()
    
    _sync_showing_or_hiding_ready_control(client_id, checkbox, checkbox_label, cannot_enter_game_text)
    if GAME_SETUP_DATA.can_client_enter_game(client_id):
        gui_hide(cannot_enter_game_text)
    else:
        gui_show(cannot_enter_game_text)
    
    yield END()

# ----- on-events/syncing -----

@label()
def _on_ready_checkbox_clicked():
    client_id = get_variable("client_id")
    GAME_SETUP_DATA = get_game_setup_data()
    checkbox, checkbox_label, cannot_enter_game_text = _get_ready_control_gui_elements()
    
    if checkbox.value:
        is_successful = GAME_SETUP_DATA.try_client_ready(client_id)
        if not is_successful:
            checkbox.value = False
            gui_represent_patched(checkbox)
    else:
        GAME_SETUP_DATA.client_unready(client_id)
    
    yield END()

@label()
def _sync_ready_checkbox_on_client_ready_changed():
    IS_READY = get_variable("IS_READY")
    checkbox, checkbox_label, cannot_enter_game_text = _get_ready_control_gui_elements()
    
    # note the checkbox might be hidden (if the client currently can't ready)
    if checkbox.value != IS_READY:
        checkbox.value = IS_READY
        gui_represent_patched(checkbox)
    
    yield END()

@label()
def _sync_ready_checkbox_on_can_client_ready_changed():
    client_id = get_variable("client_id")
    checkbox, checkbox_label, cannot_enter_game_text = _get_ready_control_gui_elements()
    
    _sync_showing_or_hiding_ready_control(client_id, checkbox, checkbox_label, cannot_enter_game_text)
    
    yield END()

@label()
def _sync_ready_checkbox_on_can_client_enter_game_changed():
    client_id = get_variable("client_id")
    checkbox, checkbox_label, cannot_enter_game_text = _get_ready_control_gui_elements()
    
    _sync_showing_or_hiding_cannot_enter_game_text(client_id, cannot_enter_game_text)
    
    yield END()

# ----- misc -----

def _sync_showing_or_hiding_ready_control(client_id, checkbox, checkbox_label, cannot_enter_game_text):
    GAME_SETUP_DATA = get_game_setup_data()
    show = GAME_SETUP_DATA.can_client_ready(client_id)
    if show != checkbox.is_hidden:
        return
    if show and checkbox.is_hidden:
        gui_show(checkbox)
        gui_show(checkbox_label)
        if GAME_SETUP_DATA.can_client_enter_game(client_id):
            gui_hide(cannot_enter_game_text)
        else:
            gui_show(cannot_enter_game_text)
    else:
        gui_hide(checkbox)
        gui_hide(checkbox_label)
        gui_hide(cannot_enter_game_text)
    gui_represent_patched(checkbox)
    gui_represent_patched(checkbox_label)
    gui_represent_patched(cannot_enter_game_text)

def _sync_showing_or_hiding_cannot_enter_game_text(client_id, cannot_enter_game_text, skip_represent=False):
    GAME_SETUP_DATA = get_game_setup_data()
    can_enter_game = GAME_SETUP_DATA.can_client_enter_game(client_id)
    if can_enter_game == cannot_enter_game_text.is_hidden:
        return
    if can_enter_game:
        gui_hide(cannot_enter_game_text)
    else:
        gui_show(cannot_enter_game_text)
    if not skip_represent:
        gui_represent_patched(cannot_enter_game_text)

# ----- setter/getter wrappers -----

def _get_ready_control_gui_elements():
    elements = get_variable(_READY_CONTROL_GUI_ELEMENTS_VAR_NAME)
    return elements[0], elements[1], elements[2]

def _set_ready_control_gui_elements(checkbox, checkbox_label, cannot_enter_game_text):
    set_variable(_READY_CONTROL_GUI_ELEMENTS_VAR_NAME, (checkbox, checkbox_label, cannot_enter_game_text))

_READY_CONTROL_GUI_ELEMENTS_VAR_NAME = "_gui_console_selection_ready_control_gui_elements"
