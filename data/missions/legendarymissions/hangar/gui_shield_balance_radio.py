from enum import Enum

from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import END, get_variable, set_variable
from sbs_utils.procedural.signal import signal_register
from sbs_utils.procedural.space_objects import set_engineering_value, get_engineering_value
from sbs_utils.procedural.gui import gui_blank, gui_checkbox, gui_message, gui_row

from data.missions.common.library_function_patches import gui_represent_patched
from data.missions.common.gui_color_scheme import color_text, color_background

# ----- creation -----

def create_shield_balance_radio(craft_id):
    current_balance = _get_shield_balance(craft_id)
    
    # I considered using gui_vradio, but unfortunately its color can't be customized
    shield_balance_to_checkbox = {}
    for shield_balance in ShieldBalance:
        gui_row(style=f"row-height:8px;background:{color_background()};")
        gui_blank()
        gui_row(style="row-height:36px;")
        checkbox = gui_checkbox(shield_balance.value, style=f"font:gui-2;color:{color_text()};", data={"CRAFT_ID": craft_id, "SHIELD_BALANCE": shield_balance})
        
        gui_message(checkbox, _shield_balance_radio_on_checkbox_toggled)
        shield_balance_to_checkbox[shield_balance] = checkbox
    
    shield_balance_to_checkbox[current_balance].value = True
    
    _set_shield_balance_radio_checkboxes(shield_balance_to_checkbox)
    
    signal_register(signal_shield_balance_changed(craft_id), _shield_balance_radio_on_shield_balance_changed, is_temporary=True)

# ----- on-events -----

@label()
def _shield_balance_radio_on_checkbox_toggled():
    craft_id = get_variable("CRAFT_ID")
    new_shield_balance = get_variable("SHIELD_BALANCE")
    old_shield_balance = _get_shield_balance(craft_id)
    shield_balance_to_checkbox = _get_shield_balance_radio_checkboxes()
    
    if old_shield_balance == new_shield_balance:
        checkbox = shield_balance_to_checkbox[new_shield_balance]
        checkbox.value = True
        gui_represent_patched(checkbox)
        yield END()
    
    _set_shield_balance(craft_id, new_shield_balance)
    
    old_checkbox = shield_balance_to_checkbox[old_shield_balance]
    new_checkbox = shield_balance_to_checkbox[new_shield_balance]
    old_checkbox.value = False
    new_checkbox.value = True
    gui_represent_patched(old_checkbox)
    gui_represent_patched(new_checkbox)
    
    yield END()

@label()
def _shield_balance_radio_on_shield_balance_changed():
    craft_id = get_variable("CRAFT_ID")
    shield_balance = _get_shield_balance(craft_id)
    shield_balance_to_checkbox = _get_shield_balance_radio_checkboxes()
    
    old_checkbox = None
    for checkbox in shield_balance_to_checkbox.values():
        if checkbox.value:
            old_checkbox = checkbox
            break
    if old_checkbox is not None:
        old_checkbox.value = False
        gui_represent_patched(old_checkbox)
    
    new_checkbox = shield_balance_to_checkbox[shield_balance]
    new_checkbox.value = True
    gui_represent_patched(new_checkbox)
    
    yield END()

# ----- constants -----

class ShieldBalance(Enum):
    ALL_FRONT = "All Front"
    BALANCED = "Balanced"
    ALL_REAR = "All Rear"

_INITIAL_SHIELD_BALANCE_VAR_NAME = "_initial_shield_balance"

# ----- getters/setters -----

def set_shield_balance_to_next(craft_id):
    shield_balance = _get_shield_balance(craft_id)
    match shield_balance:
        case ShieldBalance.ALL_FRONT:
            _set_shield_balance(craft_id, ShieldBalance.BALANCED)
        case ShieldBalance.BALANCED:
            _set_shield_balance(craft_id, ShieldBalance.ALL_REAR)
        case ShieldBalance.ALL_REAR:
            _set_shield_balance(craft_id, ShieldBalance.ALL_FRONT)
        case _:
            _set_shield_balance(craft_id, ShieldBalance.BALANCED)

def _set_shield_balance(craft_id, shield_balance):
    match shield_balance:
        case ShieldBalance.ALL_FRONT:
            set_engineering_value(craft_id, _FRONT_SHIELD_ENGINEERING_VALUE_KEY, 2.0)
            set_engineering_value(craft_id, _REAR_SHIELD_ENGINEERING_VALUE_KEY, 0.0)
        case ShieldBalance.BALANCED:
            set_engineering_value(craft_id, _FRONT_SHIELD_ENGINEERING_VALUE_KEY, 1.0)
            set_engineering_value(craft_id, _REAR_SHIELD_ENGINEERING_VALUE_KEY, 1.0)
        case ShieldBalance.ALL_REAR:
            set_engineering_value(craft_id, _FRONT_SHIELD_ENGINEERING_VALUE_KEY, 0.0)
            set_engineering_value(craft_id, _REAR_SHIELD_ENGINEERING_VALUE_KEY, 2.0)
        case _:
            pass

def _get_shield_balance(craft_id):
    front_shield_power = get_engineering_value(craft_id, _FRONT_SHIELD_ENGINEERING_VALUE_KEY)
    #rear_shield_power = get_engineering_value(craft_id, _REAR_SHIELD_ENGINEERING_VALUE_KEY)
    if 1.5 < front_shield_power:
        return ShieldBalance.ALL_FRONT
    elif front_shield_power < 0.5:
        return ShieldBalance.ALL_REAR
    else:
        return ShieldBalance.BALANCED

_FRONT_SHIELD_ENGINEERING_VALUE_KEY = "front shield"
_REAR_SHIELD_ENGINEERING_VALUE_KEY = "rear shield"

def _set_shield_balance_radio_checkboxes(checkboxes):
    set_variable(_SHIELD_BALANCE_RADIO_CHECKBOXES_VAR_NAME, checkboxes)

def _get_shield_balance_radio_checkboxes():
    return get_variable(_SHIELD_BALANCE_RADIO_CHECKBOXES_VAR_NAME)

_SHIELD_BALANCE_RADIO_CHECKBOXES_VAR_NAME = "_shield_balance_radio_checkboxes"

# ----- signals -----

def signal_shield_balance_changed(craft_id):
    return f"shield_balance_changed_{craft_id}"
