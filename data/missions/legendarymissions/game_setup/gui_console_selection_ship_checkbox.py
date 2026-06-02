"""
Creating and updating/syncing the checkboxes for player ships in console selection
"""

from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import END, get_variable, set_variable, task_schedule, AWAIT
from sbs_utils.procedural.signal import signal_register
from sbs_utils.procedural.gui import gui_section, gui_text, gui_checkbox, gui_message, gui_show, gui_hide
from sbs_utils.procedural.timers import delay_app

from data.missions.common.library_function_patches import gui_represent_patched
from data.missions.common.controller_vessel_types_data import get_vessel_types_data
from data.missions.common.gui_color_scheme import color_text, color_text_secondary

from model_game_setup_data import signal_game_setup_data_client_ready_changed, signal_game_setup_data_player_ship_count_changed
from model_player_ship_setup_data import signal_player_ship_setup_data_selection_changed, signal_player_ship_setup_data_name_changed, signal_player_ship_setup_data_ship_type_changed, signal_player_ship_setup_data_is_destroyed_changed
from controller_game_setup_data import get_game_setup_data

# ----- creation -----

def create_ship_checkbox(ship, client_id, x_left, y_top, x_mid, x_right):
    y_bottom = f"{y_top}+{ship_checkbox_height()}px"
    
    gui_section(style=f"area:{x_mid},{y_top},{x_right},{y_bottom};")
    checkbox = gui_checkbox("", style=f"color:{color_text()};", data={"SHIP": ship})
    checkbox.value = ship.is_selected_by_client(client_id)
    
    # Use separate text elements for the labels, partly so that
    # long ship names can spill off horizontally instead of
    # overlapping with the checkbox(es) below,
    # but also to allow many different labels to be displayed fancily
    
    gui_section(style=f"area:{x_mid},{y_top},{x_right},{y_bottom};")
    number_label = gui_text(_get_ship_checkbox_number_label_string(ship), style=f"font:gui-3;justify:left;padding:34px,1px,10px,0;color:{color_text()};")
    
    gui_section(style=f"area:{x_mid},{y_top},{x_right},{y_bottom};")
    connections_label = gui_text(_get_ship_checkbox_connections_label_string(ship), style=f"font:gui-1;justify:left;padding:34px,27px,10px,0;color:{color_text_secondary()};")
    
    # don't let area coordinates go less than about -990,
    # otherwise the element runs into issues with showing/hiding
    
    gui_section(style=f"area:0-800,{y_top},{x_right},{y_bottom};")
    primary_label = gui_text(_get_ship_checkbox_primary_label_string(ship), style=f"font:gui-3;justify:right;padding:0,1px,10px,0;color:{color_text()};")
    
    gui_section(style=f"area:0-800,{y_top},{x_right},{y_bottom};")
    secondary_label = gui_text(_get_ship_checkbox_secondary_label_string(ship), style=f"font:gui-1;justify:right;padding:0,27px,10px,0;color:{color_text_secondary()};")
    
    gui_section(style=f"area:{x_left},{y_top},{x_mid},{y_bottom};")
    # Delay setting the actual string of text to display,
    # to avoid it showing for a moment before the element gets hidden
    destroyed_text = gui_text("", style="font:gui-3;justify:right;padding:0,10px,8px,0;color:#f44;background:#0004;")
    
    _add_to_ship_checkbox_gui_elements(ship.number, checkbox, number_label, connections_label, primary_label, secondary_label, destroyed_text)
    
    gui_message(checkbox, _on_ship_checkbox_clicked)
    
    task_schedule(_update_ship_checkbox_after_delay, data={"SHIP_NUMBER": ship.number, "DESTROYED_TEXT": destroyed_text})

@label()
def _update_ship_checkbox_after_delay():
    # If an element is hidden prior to it being presented for the first time,
    # then it will never show again.
    # https://github.com/artemis-sbs/LegendaryMissions/issues/513#issuecomment-3931007180
    # So work around this by adding a short delay before hiding the element,
    # so that the element will (hopefully) have been presented already by the
    # time gui_hide is called.
    yield AWAIT(delay_app(0))
    ship_number = get_variable("SHIP_NUMBER")
    GAME_SETUP_DATA = get_game_setup_data()
    
    destroyed_text = get_variable("DESTROYED_TEXT")
    destroyed_text.value = _get_ship_checkbox_destroyed_message_string()
    # represent will happen later, inside _sync_showing_or_hiding_destroyed_text
    
    show = ship_number <= GAME_SETUP_DATA.player_ship_count
    _gui_show_or_hide_ship_checkbox(ship_number, show)
    if show:
        ship = GAME_SETUP_DATA.get_player_ship_by_number(ship_number)
        _sync_showing_or_hiding_destroyed_text(ship, destroyed_text)
    # if entire checkbox is hiding, then destroyed_text would've
    # already been hidden in _gui_show_or_hide_ship_checkbox
    
    yield END()

def set_up_syncing_for_all_ship_checkboxes(client_id):
    signal_register(signal_player_ship_setup_data_selection_changed(client_id), _sync_ship_checkbox_on_this_client_ship_selection_changed, is_temporary=True)
    signal_register(signal_player_ship_setup_data_selection_changed(), _sync_ship_checkbox_on_any_client_ship_selection_changed, is_temporary=True)
    signal_register(signal_game_setup_data_client_ready_changed(), _sync_ship_checkbox_on_any_client_ready_changed, is_temporary=True)
    signal_register(signal_player_ship_setup_data_name_changed(), _sync_ship_checkbox_on_ship_name_changed, is_temporary=True)
    signal_register(signal_player_ship_setup_data_ship_type_changed(), _sync_ship_checkbox_on_ship_type_changed, is_temporary=True)
    signal_register(signal_game_setup_data_player_ship_count_changed(), _sync_ship_checkbox_on_ship_count_changed, is_temporary=True)
    signal_register(signal_player_ship_setup_data_is_destroyed_changed(), _sync_ship_checkbox_on_ship_destroyed_changed, is_temporary=True)

# ----- on-events/syncing -----

@label()
def _on_ship_checkbox_clicked():
    GAME_SETUP_DATA = get_game_setup_data()
    client_id = get_variable("client_id")
    checkbox = get_variable("__ITEM__")
    ship = get_variable("SHIP")
    
    if checkbox.value:
        GAME_SETUP_DATA.switch_ship(client_id, ship.number)
    elif ship.is_selected_by_client(client_id):
        # Cancel attempts to deselect the checkbox of your selected ship
        checkbox.value = True
        gui_represent_patched(checkbox)
    GAME_SETUP_DATA.client_unready(client_id)
    
    yield END()

@label()
def _sync_ship_checkbox_on_this_client_ship_selection_changed():
    ship = get_variable("SHIP")
    selected = get_variable("SELECTED")
    checkbox, number_label, connections_label, primary_label, secondary_label, destroyed_text = _get_ship_checkbox_gui_elements(ship.number)
    if checkbox is None:
        yield END()
    
    if checkbox.value != selected:
        checkbox.value = selected
        gui_represent_patched(checkbox)
    
    yield END()

@label()
def _sync_ship_checkbox_on_any_client_ship_selection_changed():
    ship = get_variable("SHIP")
    _sync_connections_label_text(ship)
    yield END()

@label()
def _sync_ship_checkbox_on_any_client_ready_changed():
    ready_changed_client_id = get_variable("CLIENT_ID")
    GAME_SETUP_DATA = get_game_setup_data()
    ship = GAME_SETUP_DATA.get_selected_ship(ready_changed_client_id)
    if ship is not None:
        _sync_connections_label_text(ship)
    yield END()

@label()
def _sync_ship_checkbox_on_ship_name_changed():
    ship = get_variable("SHIP")
    checkbox, number_label, connections_label, primary_label, secondary_label, destroyed_text = _get_ship_checkbox_gui_elements(ship.number)
    if checkbox is None:
        yield END()
    
    new_primary_label_string = _get_ship_checkbox_primary_label_string(ship)
    if primary_label.value != new_primary_label_string:
        primary_label.value = new_primary_label_string
        gui_represent_patched(primary_label)
    
    yield END()

@label()
def _sync_ship_checkbox_on_ship_type_changed():
    ship = get_variable("SHIP")
    checkbox, number_label, connections_label, primary_label, secondary_label, destroyed_text = _get_ship_checkbox_gui_elements(ship.number)
    if checkbox is None:
        yield END()
    
    new_secondary_label_string = _get_ship_checkbox_secondary_label_string(ship)
    if secondary_label.value != new_secondary_label_string:
        secondary_label.value = new_secondary_label_string
        gui_represent_patched(secondary_label)
    
    yield END()

@label()
def _sync_ship_checkbox_on_ship_count_changed():
    old_player_ship_count = get_variable("OLD_PLAYER_SHIP_COUNT")
    GAME_SETUP_DATA = get_game_setup_data()
    player_ship_count = GAME_SETUP_DATA.player_ship_count
    
    # +1 makes low exclusive and high inclusive
    low_ship_number = min(old_player_ship_count, player_ship_count) + 1
    high_ship_number = max(old_player_ship_count, player_ship_count) + 1
    show = old_player_ship_count < player_ship_count
    for ship_number in range(low_ship_number, high_ship_number):
        _gui_show_or_hide_ship_checkbox(ship_number, show)
    
    yield END()

@label()
def _sync_ship_checkbox_on_ship_destroyed_changed():
    ship = get_variable("SHIP")
    checkbox, number_label, connections_label, primary_label, secondary_label, destroyed_text = _get_ship_checkbox_gui_elements(ship.number)
    if checkbox is None:
        yield END()
    
    if not checkbox.is_hidden:
        _sync_showing_or_hiding_destroyed_text(ship, destroyed_text)
    
    yield END()

# ----- misc -----

def ship_checkbox_height():
    return 52

def _get_ship_checkbox_number_label_string(ship):
    return f"Ship {ship.number}"

def _get_ship_checkbox_connections_label_string(ship):
    GAME_SETUP_DATA = get_game_setup_data()
    connected_client_ids = ship.get_selected_by_clients(exclude_server=True, exclude_operator_mode=True)
    readied_clients_count = sum(1 for client_id in connected_client_ids if GAME_SETUP_DATA.is_client_ready(client_id))
    return f"{readied_clients_count} ready / {len(connected_client_ids)} connections"

def _get_ship_checkbox_primary_label_string(ship):
    return ship.name

def _get_ship_checkbox_secondary_label_string(ship):
    VESSEL_TYPES_DATA = get_vessel_types_data()
    ship_type = VESSEL_TYPES_DATA.get_ship_type_from_key(ship.ship_type_key)
    return f"{ship_type.origin} {ship_type.ship_type_name}"

def _get_ship_checkbox_destroyed_message_string():
    return "LOST"

def _should_show_destroyed_text(ship):
    return ship.is_destroyed

def _gui_show_or_hide_ship_checkbox(ship_number, show):
    GAME_SETUP_DATA = get_game_setup_data()
    checkbox, number_label, connections_label, primary_label, secondary_label, destroyed_text = _get_ship_checkbox_gui_elements(ship_number)
    if checkbox is None or show != checkbox.is_hidden:
        return
    if show and checkbox.is_hidden:
        gui_show(checkbox)
        gui_show(number_label)
        gui_show(connections_label)
        gui_show(primary_label)
        gui_show(secondary_label)
        ship = GAME_SETUP_DATA.get_player_ship_by_number(ship_number)
        if _should_show_destroyed_text(ship):
            gui_show(destroyed_text)
        else:
            gui_hide(destroyed_text)
    else:
        gui_hide(checkbox)
        gui_hide(number_label)
        gui_hide(connections_label)
        gui_hide(primary_label)
        gui_hide(secondary_label)
        gui_hide(destroyed_text)
    gui_represent_patched(checkbox)
    gui_represent_patched(number_label)
    gui_represent_patched(connections_label)
    gui_represent_patched(primary_label)
    gui_represent_patched(secondary_label)
    gui_represent_patched(destroyed_text)

def _sync_connections_label_text(ship):
    checkbox, number_label, connections_label, primary_label, secondary_label, destroyed_text = _get_ship_checkbox_gui_elements(ship.number)
    if checkbox is None:
        return
    
    new_connections_label_string = _get_ship_checkbox_connections_label_string(ship)
    if connections_label.value != new_connections_label_string:
        connections_label.value = new_connections_label_string
        gui_represent_patched(connections_label)

def _sync_showing_or_hiding_destroyed_text(ship, destroyed_text, skip_represent=False):
    should_show = _should_show_destroyed_text(ship)
    if should_show != destroyed_text.is_hidden:
        return
    if should_show:
        gui_show(destroyed_text)
    else:
        gui_hide(destroyed_text)
    if not skip_represent:
        gui_represent_patched(destroyed_text)

# ----- setter/getter wrappers -----

def _get_ship_checkbox_gui_elements(ship_number):
    all_gui_elements = get_variable(_SHIP_CHECKBOX_GUI_ELEMENTS_VAR_NAME)
    if ship_number not in all_gui_elements:
        return None, None, None, None, None, None
    gui_elements = all_gui_elements[ship_number]
    return gui_elements[0], gui_elements[1], gui_elements[2], gui_elements[3], gui_elements[4], gui_elements[5]

def _add_to_ship_checkbox_gui_elements(ship_number, checkbox, number_label, connections_label, primary_label, secondary_label, destroyed_text):
    all_gui_elements = get_variable(_SHIP_CHECKBOX_GUI_ELEMENTS_VAR_NAME)
    if all_gui_elements is None:
        all_gui_elements = {}
        set_variable(_SHIP_CHECKBOX_GUI_ELEMENTS_VAR_NAME, all_gui_elements)
    all_gui_elements[ship_number] = (checkbox, number_label, connections_label, primary_label, secondary_label, destroyed_text)

_SHIP_CHECKBOX_GUI_ELEMENTS_VAR_NAME = "_gui_console_selection_ship_checkbox_gui_elements"
