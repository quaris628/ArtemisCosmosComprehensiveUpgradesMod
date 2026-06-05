from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import END, get_variable, set_variable
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.signal import signal_register
from sbs_utils.procedural.gui import gui_blank, gui_checkbox, gui_message, gui_row
from sbs_utils.procedural.query import to_space_object

from data.missions.common.library_function_patches import gui_represent_patched
from data.missions.common.gui_color_scheme import color_text, color_background

from hangar import get_available_ordinance_types

# ----- creation -----

def create_ordinance_type_radio(craft_object, available_ordinance_types):
    current_ordinance_type = _get_ordinance_type_selection(craft_object)
    
    # I considered using gui_vradio, but unfortunately its color can't be customized
    ordinance_type_to_checkbox = {}
    _set_available_ordinance_types(craft_object.id, available_ordinance_types)
    for ordinance_type in available_ordinance_types:
        gui_row(style=f"row-height:8px;background:{color_background()};")
        gui_blank()
        gui_row(style="row-height:36px;")
        checkbox = gui_checkbox(ordinance_type, style=f"font:gui-2;color:{color_text()};", data={"CRAFT_ID": craft_object.id, "ORDINANCE_TYPE": ordinance_type})
        
        gui_message(checkbox, _ordinance_type_radio_on_checkbox_toggled)
        ordinance_type_to_checkbox[ordinance_type] = checkbox
    
    ordinance_type_to_checkbox[current_ordinance_type].value = True
    
    _set_ordinance_type_radio_checkboxes(ordinance_type_to_checkbox)
    
    signal_register(signal_ordinance_type_changed(craft_object.id), _ordinance_type_radio_on_ordinance_type_changed, is_temporary=True)

# ----- on-events -----

@label()
def _ordinance_type_radio_on_checkbox_toggled():
    craft_id = get_variable("CRAFT_ID")
    craft_object = to_space_object(craft_id)
    if craft_object is None:
        yield END()
    new_ordinance_type = get_variable("ORDINANCE_TYPE")
    old_ordinance_type = _get_ordinance_type_selection(craft_object)
    ordinance_type_to_checkbox = _get_ordinance_type_radio_checkboxes()
    
    if old_ordinance_type == new_ordinance_type:
        checkbox = ordinance_type_to_checkbox[new_ordinance_type]
        checkbox.value = True
        gui_represent_patched(checkbox)
        yield END()
    
    _set_ordinance_type_selection(craft_object, new_ordinance_type)
    
    old_checkbox = ordinance_type_to_checkbox[old_ordinance_type]
    new_checkbox = ordinance_type_to_checkbox[new_ordinance_type]
    old_checkbox.value = False
    new_checkbox.value = True
    gui_represent_patched(old_checkbox)
    gui_represent_patched(new_checkbox)
    
    yield END()

@label()
def _ordinance_type_radio_on_ordinance_type_changed():
    craft_id = get_variable("CRAFT_ID")
    craft_object = to_space_object(craft_id)
    if craft_object is None:
        yield END()
    ordinance_type = _get_ordinance_type_selection(craft_object)
    ordinance_type_to_checkbox = _get_ordinance_type_radio_checkboxes()
    
    old_checkbox = None
    for checkbox in ordinance_type_to_checkbox.values():
        if checkbox.value:
            old_checkbox = checkbox
            break
    if old_checkbox is not None:
        old_checkbox.value = False
        gui_represent_patched(old_checkbox)
    
    new_checkbox = ordinance_type_to_checkbox[ordinance_type]
    new_checkbox.value = True
    gui_represent_patched(new_checkbox)
    
    yield END()

# ----- getters/setters -----

def set_ordinance_type_to_next(craft_object):
    available_ordinance_types = _get_available_ordinance_types(craft_object.id)
    old_ordinance_type = _get_ordinance_type_selection(craft_object)
    
    index = available_ordinance_types.index(old_ordinance_type)
    index += 1
    if index == len(available_ordinance_types):
        index = 0
    new_ordinance_type = available_ordinance_types[index]
    _set_ordinance_type_selection(craft_object, new_ordinance_type)

def _get_ordinance_type_selection(craft_object):
    # Might return None the first time this craft object is launched
    ordinance_type = craft_object.data_set.get(_ORDINANCE_TYPE_SELECTION_BLOB_KEY, 0)
    if ordinance_type is None:
        available_ordinance_types = get_available_ordinance_types(craft_object)
        if len(available_ordinance_types) == 0:
            return None
        return available_ordinance_types[0]
    return ordinance_type

def _set_ordinance_type_selection(craft_object, ordinance_type):
    craft_object.data_set.set(_ORDINANCE_TYPE_SELECTION_BLOB_KEY, ordinance_type, 0)

_ORDINANCE_TYPE_SELECTION_BLOB_KEY = "torpedoTubeCurrentType"

def _set_available_ordinance_types(craft_id, available_ordinance_types):
    set_inventory_value(craft_id, _AVAILABLE_ORDINANCE_TYPES_INVENTORY_KEY, available_ordinance_types)

def _get_available_ordinance_types(craft_id):
    return get_inventory_value(craft_id, _AVAILABLE_ORDINANCE_TYPES_INVENTORY_KEY)

_AVAILABLE_ORDINANCE_TYPES_INVENTORY_KEY = "_available_ordinance_types"

def _set_ordinance_type_radio_checkboxes(checkboxes):
    set_variable(_ORDINANCE_TYPE_RADIO_CHECKBOXES_VAR_NAME, checkboxes)

def _get_ordinance_type_radio_checkboxes():
    return get_variable(_ORDINANCE_TYPE_RADIO_CHECKBOXES_VAR_NAME)

_ORDINANCE_TYPE_RADIO_CHECKBOXES_VAR_NAME = "_ordinance_type_radio_checkboxes"

# ----- signals -----

def signal_ordinance_type_changed(craft_id):
    return f"ordinance_type_changed_{craft_id}"
