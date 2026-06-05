
from sbs_utils.mast.label import label
from sbs_utils.procedural.comms import comms_broadcast
from sbs_utils.procedural.execution import END, get_variable, set_variable
from sbs_utils.procedural.signal import signal_register
from sbs_utils.procedural.gui import gui_message, gui_hide
from sbs_utils.procedural.query import to_space_object

from data.missions.common.library_function_patches import gui_represent_patched, gui_dropdown_patched
from data.missions.common.gui_color_scheme import color_text

from hangar import hangar_clear_dock, hangar_get_dock, hangar_get_valid_dock_ids, hangar_set_dock

# ----- creation -----

def create_home_docks_dropdown(craft_id):
    current_dock_id = hangar_get_dock(craft_id)
    valid_dock_ids = hangar_get_valid_dock_ids(craft_id)
    
    _set_valid_dock_ids(valid_dock_ids)
    names_list = _get_unique_dock_names_list()
    current_dock_name = _get_unique_dock_name(current_dock_id)
    
    dropdown = gui_dropdown_patched(names_list, value=current_dock_name, style=f"font:gui-2;color:{color_text()};", data={"CRAFT_ID": craft_id})
    
    _set_home_docks_dropdown(dropdown)
    
    gui_message(dropdown, _home_docks_dropdown_on_dropdown_changed)
    
    signal_register(signal_potential_valid_dock_destroyed(), _home_docks_dropdown_on_potential_valid_dock_destroyed, is_temporary=True)

# ----- on-events -----

@label()
def _home_docks_dropdown_on_dropdown_changed():
    craft_id = get_variable("CRAFT_ID")
    dropdown = _get_home_docks_dropdown()
    current_dock_id = hangar_get_dock(craft_id)
    
    current_dock_name = _get_unique_dock_name(current_dock_id)
    if current_dock_name != dropdown.value:
        new_dock_id = _get_dock_id_from_unique_name(dropdown.value)
        if to_space_object(new_dock_id) is not None:
            hangar_set_dock(craft_id, new_dock_id)
    
    yield END()

@label()
def _home_docks_dropdown_on_potential_valid_dock_destroyed():
    destroyed_id = get_variable("DESTROYED_ID")
    dropdown = _get_home_docks_dropdown()
    craft_id = dropdown.data["CRAFT_ID"]
    current_dock_id = hangar_get_dock(craft_id)
    
    if not _remove_valid_dock_id(destroyed_id):
        yield END()
    
    names_list = _get_unique_dock_names_list()
    if len(names_list) == 0:
        hangar_clear_dock(craft_id)
        dropdown.values_as_csv = "None"
        dropdown.value = "None"
        gui_hide(dropdown)
        comms_broadcast(craft_id, "No docking locations remain")
        # Note it is possible for a player single-seat craft to have no valid docks
        # but for the simulation to still be running. E.g. all pirate player ships and
        # stations are destroyed but a tsn player ship still exists, or vice versa.
    else:
        dropdown.values_as_list = names_list
        if current_dock_id == destroyed_id: # if current dock no longer in values
            new_dock_name = names_list[0]
            new_dock_id = _get_dock_id_from_unique_name(new_dock_name)
            hangar_set_dock(craft_id, new_dock_id)
            dropdown.value = new_dock_name
            comms_broadcast(craft_id, f"Home dock is now {new_dock_name}")
    gui_represent_patched(dropdown)
    
    yield END()

# ----- getters/setters -----

def _set_valid_dock_ids(dock_ids):
    ids_to_unique_names = {}
    unique_names_to_ids = {}
    original_name_to_suffix_number = {}
    for dock_id in dock_ids:
        dock_object = to_space_object(dock_id)
        name = dock_object.name.replace(",", "")
        if name not in original_name_to_suffix_number:
            original_name_to_suffix_number[name] = 0
            ids_to_unique_names[dock_id] = name
            unique_names_to_ids[name] = dock_id
        else:
            suffix_number = original_name_to_suffix_number[name] + 1
            original_name_to_suffix_number[name] = suffix_number
            unique_name = f"{name} {suffix_number}"
            ids_to_unique_names[dock_id] = unique_name
            unique_names_to_ids[unique_name] = dock_id
    
    set_variable(_HOME_DOCKS_DROPDOWN_IDS_TO_NAMES_VAR_NAME, ids_to_unique_names)
    set_variable(_HOME_DOCKS_DROPDOWN_NAMES_TO_IDS_VAR_NAME, unique_names_to_ids)

def _remove_valid_dock_id(dock_id):
    ids_to_unique_names = get_variable(_HOME_DOCKS_DROPDOWN_IDS_TO_NAMES_VAR_NAME)
    if dock_id not in ids_to_unique_names:
        return False
    unique_names_to_ids = get_variable(_HOME_DOCKS_DROPDOWN_NAMES_TO_IDS_VAR_NAME)
    
    unique_name = ids_to_unique_names[dock_id]
    ids_to_unique_names.pop(dock_id)
    unique_names_to_ids.pop(unique_name)
    
    set_variable(_HOME_DOCKS_DROPDOWN_IDS_TO_NAMES_VAR_NAME, ids_to_unique_names)
    set_variable(_HOME_DOCKS_DROPDOWN_NAMES_TO_IDS_VAR_NAME, unique_names_to_ids)
    return True

def _get_unique_dock_names_list():
    return sorted(list(get_variable(_HOME_DOCKS_DROPDOWN_NAMES_TO_IDS_VAR_NAME).keys()))

def _get_unique_dock_name(dock_id):
    ids_to_unique_names = get_variable(_HOME_DOCKS_DROPDOWN_IDS_TO_NAMES_VAR_NAME)
    if dock_id not in ids_to_unique_names:
        return None
    return ids_to_unique_names[dock_id]
    
def _get_dock_id_from_unique_name(unique_name):
    unique_names_to_ids = get_variable(_HOME_DOCKS_DROPDOWN_NAMES_TO_IDS_VAR_NAME)
    return unique_names_to_ids[unique_name]

_HOME_DOCKS_DROPDOWN_IDS_TO_NAMES_VAR_NAME = "_home_docks_dropdown_ids_to_names"
_HOME_DOCKS_DROPDOWN_NAMES_TO_IDS_VAR_NAME = "_home_docks_dropdown_names_to_ids"

def _set_home_docks_dropdown(dropdown):
    set_variable(_HOME_DOCKS_DROPDOWN_DROPDOWN_VAR_NAME, dropdown)

def _get_home_docks_dropdown():
    return get_variable(_HOME_DOCKS_DROPDOWN_DROPDOWN_VAR_NAME)

_HOME_DOCKS_DROPDOWN_DROPDOWN_VAR_NAME = "_home_docks_dropdown_dropdown"

# ----- signals -----

def signal_potential_valid_dock_destroyed():
    return "potential_valid_dock_destroyed"
