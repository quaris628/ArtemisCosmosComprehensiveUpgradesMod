"""
Creating and updating/syncing the checkboxes for player ships in console selection
"""
from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import task_schedule, AWAIT, END, get_variable, set_variable
from sbs_utils.procedural.signal import signal_register
from sbs_utils.procedural.gui import gui_section, gui_text, gui_checkbox, gui_hide, gui_show, gui_message
from sbs_utils.procedural.timers import delay_app

from data.missions.common.library_function_patches import gui_represent_patched
from data.missions.common.gui_color_scheme import color_text, color_text_secondary

from model_console_slot import signal_console_slot_is_exclusively_taken_changed
from model_player_ship_setup_data import signal_player_ship_setup_data_selection_changed
from controller_game_setup_data import get_game_setup_data

# ----- creation -----

def create_console_checkbox(console_identifier, client_id, x_left, y_top, x_mid, x_right):
    y_bottom = f"{y_top}+{console_checkbox_height()}px"
    
    console_slot = _get_console_slot(console_identifier, client_id)
    
    gui_section(style=f"area:{x_left},{y_top},{x_mid},{y_bottom};")
    checkbox = gui_checkbox("", style=f"color:{color_text()};", data={"CONSOLE_IDENTIFIER": console_identifier})
    checkbox.value = console_slot.is_selected_by_client(client_id)
    
    # Use separate text elements for the labels, partly so that
    # long console names can spill off horizontally instead of
    # overlapping with the checkbox(es) below,
    # but also to allow many different labels to be displayed fancily
    
    gui_section(style=f"area:{x_left},{y_top},1000,{y_bottom};")
    primary_label = gui_text(_get_console_checkbox_primary_label_string(console_slot), style=f"font:gui-3;justify:left;padding:34px,3px,0,0;color:{color_text()};")
    
    gui_section(style=f"area:{x_mid},{y_top},{x_right},{y_bottom};")
    # Delay setting the actual string of text to display,
    # to avoid it showing for a moment before the element gets hidden
    taken_text = gui_text("", style="font:gui-3;padding:8px,3px,0,0;color:#0f0;background:#0004;")
    
    _add_to_console_checkbox_gui_elements(console_identifier, checkbox, primary_label, taken_text)
    
    gui_message(checkbox, _on_console_checkbox_clicked)
    
    task_schedule(_update_console_checkbox_after_delay, data={"CONSOLE_IDENTIFIER": console_identifier, "TAKEN_TEXT": taken_text})

@label()
def _update_console_checkbox_after_delay():
    # If an element is hidden prior to it being presented for the first time,
    # then it will never show again.
    # https://github.com/artemis-sbs/LegendaryMissions/issues/513#issuecomment-3931007180
    # So work around this by adding a short delay before hiding the element,
    # so that the element will (hopefully) have been presented already by the
    # time gui_hide is called.
    yield AWAIT(delay_app(0))
    client_id = get_variable("client_id")
    CONSOLE_IDENTIFIER = get_variable("CONSOLE_IDENTIFIER")
    TAKEN_TEXT = get_variable("TAKEN_TEXT")
    
    TAKEN_TEXT.value = _get_console_checkbox_taken_message_string()
    # One time I saw this label trigger after a client disconnected,
    # which caused a crash related to the selected ship being None.
    # That is (mainly) why we shouldn't assume console_slot is not None.
    console_slot = _get_console_slot(CONSOLE_IDENTIFIER, client_id)
    if console_slot is not None:
        _sync_taken_text(console_slot, TAKEN_TEXT, client_id, skip_represent=True)
        gui_represent_patched(TAKEN_TEXT)
    
    yield END()

def set_up_syncing_for_all_gui_console_checkboxes(client_id):
    signal_register(signal_player_ship_setup_data_selection_changed(client_id), _sync_console_checkbox_on_ship_selection_changed, is_temporary=True)
    signal_register(signal_console_slot_is_exclusively_taken_changed(), _sync_console_checkbox_on_console_taken_changed, is_temporary=True)

# ----- on-events/syncing -----

@label()
def _on_console_checkbox_clicked():
    GAME_SETUP_DATA = get_game_setup_data()
    client_id = get_variable("client_id")
    checkbox = get_variable("__ITEM__")
    CONSOLE_IDENTIFIER = get_variable("CONSOLE_IDENTIFIER")
    console_container = _get_console_container(CONSOLE_IDENTIFIER, client_id)
    
    if checkbox.value:
        is_successful = console_container.try_select_console(client_id, CONSOLE_IDENTIFIER)
        if not is_successful:
            checkbox.value = False
            gui_represent_patched(checkbox)
    else:
        console_container.deselect_console(client_id, CONSOLE_IDENTIFIER)
    GAME_SETUP_DATA.client_unready(client_id)
    
    yield END()

@label()
def _sync_console_checkbox_on_ship_selection_changed():
    SELECTED = get_variable("SELECTED")
    if not SELECTED:
        # If selecting more than one ship at a time ever becomes allowed,
        # or if different ships have different consoles available,
        # then something would probably need to happen for this case.
        # But at least for now, we can safely ignore de-select events.
        yield END()
    client_id = get_variable("client_id")
    SHIP = get_variable("SHIP")
    
    # Assume that all ships have the same available consoles
    for console_slot in SHIP.get_all_console_slots():
        checkbox, primary_label, taken_text = _get_console_checkbox_gui_elements(console_slot.identifier)
        if checkbox is None:
            continue
        
        if checkbox.value != console_slot.is_selected_by_client(client_id):
            checkbox.value = console_slot.is_selected_by_client(client_id)
            gui_represent_patched(checkbox)
        
        _sync_taken_text(console_slot, taken_text, client_id)
    
    yield END()

@label()
def _sync_console_checkbox_on_console_taken_changed():
    client_id = get_variable("client_id")
    CONSOLE_SLOT = get_variable("CONSOLE_SLOT")
    SHIP_NUMBER = get_variable("SHIP_NUMBER")
    GAME_SETUP_DATA = get_game_setup_data()
    # ignore if this isn't for the client's selected ship
    if SHIP_NUMBER is not None and not GAME_SETUP_DATA.get_player_ship_by_number(SHIP_NUMBER).is_selected_by_client(client_id):
        yield END()
    
    checkbox, primary_label, taken_text = _get_console_checkbox_gui_elements(CONSOLE_SLOT.identifier)
    if checkbox is None:
        yield END()
    
    _sync_taken_text(CONSOLE_SLOT, taken_text, client_id)
    
    yield END()

def _sync_taken_text(console_slot, taken_text, client_id, skip_represent=False):
    is_taken = console_slot.is_exclusively_taken_by_another_client(client_id)
    if is_taken != taken_text.is_hidden:
        return
    if is_taken and taken_text.is_hidden:
        gui_show(taken_text)
    else: # if not is_taken and not taken_text.is_hidden:
        gui_hide(taken_text)
    if not skip_represent:
        gui_represent_patched(taken_text)

# ----- misc -----

def console_checkbox_height():
    return 36

def _get_console_checkbox_primary_label_string(console_slot):
    return console_slot.display_name

def _get_console_checkbox_taken_message_string():
    # Maybe someday say "Taken by {crew member's name}"
    return "TAKEN"

def _get_console_slot(console_identifier, client_id):
    console_container = _get_console_container(console_identifier, client_id)
    if console_container is None:
        return None
    return console_container.get_console_slot(console_identifier)

def _get_console_container(console_identifier, client_id):
    GAME_SETUP_DATA = get_game_setup_data()
    if console_identifier in GAME_SETUP_DATA.get_all_console_slot_identifiers():
        return GAME_SETUP_DATA
    selected_ship = GAME_SETUP_DATA.get_selected_ship(client_id)
    if selected_ship is not None and console_identifier in selected_ship.get_all_console_slot_identifiers():
        return selected_ship
    else:
        return None

# ----- setter/getter wrappers -----

def _get_console_checkbox_gui_elements(console_identifier):
    all_gui_elements = get_variable(_CONSOLE_CHECKBOX_GUI_ELEMENTS_VAR_NAME)
    if console_identifier not in all_gui_elements:
        return None, None, None
    gui_elements = all_gui_elements[console_identifier]
    return gui_elements[0], gui_elements[1], gui_elements[2]

def _add_to_console_checkbox_gui_elements(console_identifier, checkbox, primary_label, taken_text):
    all_gui_elements = get_variable(_CONSOLE_CHECKBOX_GUI_ELEMENTS_VAR_NAME)
    if all_gui_elements is None:
        all_gui_elements = {}
        set_variable(_CONSOLE_CHECKBOX_GUI_ELEMENTS_VAR_NAME, all_gui_elements)
    all_gui_elements[console_identifier] = (checkbox, primary_label, taken_text)

_CONSOLE_CHECKBOX_GUI_ELEMENTS_VAR_NAME = "_gui_console_selection_console_checkbox_gui_elements"
