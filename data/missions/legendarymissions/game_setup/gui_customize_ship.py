from sbs_utils.procedural.execution import get_variable, set_variable

from data.missions.common.library_function_patches import gui_switch_to

def gui_switch_to_customize_ship(ship, back_label, delay_reroute_workaround=False):
    _set_customize_ship_ship(ship)
    _set_customize_ship_back_label(back_label)
    gui_switch_to("gui_customize_player_ship_main", delay_reroute_workaround=delay_reroute_workaround)

# ----- setter/getter wrappers -----

def _get_customize_ship_ship():
    return get_variable(_CUSTOMIZE_SHIP_SHIP_VAR_NAME)

def _set_customize_ship_ship(ship):
    set_variable(_CUSTOMIZE_SHIP_SHIP_VAR_NAME, ship)

_CUSTOMIZE_SHIP_SHIP_VAR_NAME = "_customize_ship_ship"

def _get_customize_ship_back_label():
    return get_variable(_CUSTOMIZE_SHIP_BACK_LABEL_VAR_NAME)

def _set_customize_ship_back_label(back_label):
    set_variable(_CUSTOMIZE_SHIP_BACK_LABEL_VAR_NAME, back_label)

_CUSTOMIZE_SHIP_BACK_LABEL_VAR_NAME = "_customize_ship_back_label"
