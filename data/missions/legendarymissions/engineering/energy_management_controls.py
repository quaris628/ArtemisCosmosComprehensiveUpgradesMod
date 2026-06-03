from sbs_utils.procedural.query import to_object
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.signal import signal_emit

# The warp resistor coil is meant as a solution for quickly draining large amounts of energy.
# A considered-but-not-done alternative solution that also (mostly) preserves the Cosmos vanilla warping energy balance is:
# 1. Make warp factors draw energy proportional to the factor squared (or some other fast-growing function)
# 2. Make engineering warp power increase warp energy-per-distance efficiency proportional to the power level squared (or some other fast-growing function)
# So to warp efficiently, the engineer would increase the power, and to warp inefficiently the helmsman would increase the warp factor.
# However, the function used to calculate the warp drive's energy draw
# does not seem to be (easily) overrideable by mission scripts, making
# implementing this alternative difficult.

def initialize_energy_management_controls(player_ship_id):
    player_ship_object = to_object(player_ship_id)
    
    old_warp_energy_cost = player_ship_object.data_set.get(data_set_key_warp_energy_cost(), 0)
    set_inventory_value(player_ship_id, inventory_key_old_warp_energy_cost(), old_warp_energy_cost)
    
    old_ship_apu_output = player_ship_object.data_set.get(data_set_key_ship_apu_output(), 0)
    set_inventory_value(player_ship_id, inventory_key_old_ship_apu_output(), old_ship_apu_output)
    
    # Initialize inventory flags oppositely, then call functions to update the ship's systems
    # (otherwise the functions would quit early since they think we're already in that state)
    set_inventory_value(player_ship_id, inventory_key_is_switch_on(switch_identifier_auto_mode()), False)
    energy_level = player_ship_object.data_set.get("energy", 0)
    set_inventory_value(player_ship_id, inventory_key_is_switch_on(switch_identifier_warp_resistor_coils()), not(_auto_should_warp_resistor_coils_be_on(energy_level)))
    set_inventory_value(player_ship_id, inventory_key_is_switch_on(switch_identifier_apu()), not(_auto_should_apu_be_on(energy_level)))
    manual_set_auto_mode(player_ship_id)

# ----- turning auto mode on/off -----

def manual_set_auto_mode(player_ship_id):
    if get_inventory_value(player_ship_id, inventory_key_is_switch_on(switch_identifier_auto_mode())):
        return
    set_inventory_value(player_ship_id, inventory_key_is_switch_on(switch_identifier_auto_mode()), True)
    
    energy_level = to_object(player_ship_id).data_set.get("energy", 0)
    set_switch_state(player_ship_id, switch_identifier_warp_resistor_coils(), _auto_should_warp_resistor_coils_be_on(energy_level), True)
    set_switch_state(player_ship_id, switch_identifier_apu(), _auto_should_apu_be_on(energy_level), True)

def manual_set_manual_mode(player_ship_id):
    set_inventory_value(player_ship_id, inventory_key_is_switch_on(switch_identifier_auto_mode()), False)

def auto_set_manual_mode(player_ship_id):
    auto_set_checkbox_state(switch_identifier_auto_mode(), False)
    set_inventory_value(player_ship_id, inventory_key_is_switch_on(switch_identifier_auto_mode()), False)

def _auto_should_warp_resistor_coils_be_on(energy_level):
    # note duplicate logic in detect_energy_changes.py
    return 4000 <= energy_level

def _auto_should_apu_be_on(energy_level):
    # note duplicate logic in detect_energy_changes.py
    return energy_level < 1000

# ----- activate/deactivate -----

def set_switch_state(player_ship_id, switch_identifier, is_new_state_on, is_auto_mode_command):
    if is_auto_mode_command:
        if not get_inventory_value(player_ship_id, inventory_key_is_switch_on(switch_identifier_auto_mode())):
            return False
        auto_set_checkbox_state(switch_identifier, is_new_state_on)
    else:
        auto_set_manual_mode(player_ship_id)
    
    if get_inventory_value(player_ship_id, inventory_key_is_switch_on(switch_identifier)) == is_new_state_on:
        return False
    set_inventory_value(player_ship_id, inventory_key_is_switch_on(switch_identifier), is_new_state_on)
    
    if switch_identifier == switch_identifier_warp_resistor_coils() and is_new_state_on:
        _activate_warp_resistor_coils(player_ship_id)
    elif switch_identifier == switch_identifier_warp_resistor_coils() and not is_new_state_on:
        _deactivate_warp_resistor_coils(player_ship_id)
    elif switch_identifier == switch_identifier_apu() and is_new_state_on:
        _activate_apu(player_ship_id)
    elif switch_identifier == switch_identifier_apu() and not is_new_state_on:
        _deactivate_apu(player_ship_id)
    return True

def auto_set_checkbox_state(checkbox_identifier, on):
    signal_emit("non_manual_change_energy_management_controls_checkbox", data={ "SWITCH_IDENTIFIER": checkbox_identifier, "ON": on })

def _activate_warp_resistor_coils(player_ship_id):
    old_warp_energy_cost = get_inventory_value(player_ship_id, inventory_key_old_warp_energy_cost())
    new_warp_energy_cost = old_warp_energy_cost * 10
    to_object(player_ship_id).data_set.set(data_set_key_warp_energy_cost(), new_warp_energy_cost, 0)

def _deactivate_warp_resistor_coils(player_ship_id):
    old_warp_energy_cost = get_inventory_value(player_ship_id, inventory_key_old_warp_energy_cost())
    to_object(player_ship_id).data_set.set(data_set_key_warp_energy_cost(), old_warp_energy_cost, 0)

def _activate_apu(player_ship_id):
    old_ship_apu_output = get_inventory_value(player_ship_id, inventory_key_old_ship_apu_output())
    to_object(player_ship_id).data_set.set(data_set_key_ship_apu_output(), old_ship_apu_output, 0)

def _deactivate_apu(player_ship_id):
    to_object(player_ship_id).data_set.set(data_set_key_ship_apu_output(), 0, 0)

# ----- constants -----

def switch_identifier_auto_mode():
    return "auto_mode"

def switch_identifier_warp_resistor_coils():
    return "warp_resistor_coils"

def switch_identifier_apu():
    return "apu"

def inventory_key_is_switch_on(checkbox_identifier):
    return f"energy_management_controls_is_{checkbox_identifier}_on"

def inventory_key_old_warp_energy_cost():
    return "energy_management_controls_old_warp_energy_cost"

def inventory_key_old_ship_apu_output():
    return "energy_management_controls_old_ship_apu_output"

def data_set_key_warp_energy_cost():
    return "warp_energy_cost"

def data_set_key_ship_apu_output():
    return "ship_apu_output"
