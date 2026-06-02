import sbs

from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import AWAIT, END, get_variable
from sbs_utils.procedural.gui import gui_section, gui_text
from sbs_utils.procedural.gui.console_types import gui_get_console_type
from sbs_utils.procedural.inventory import set_inventory_value
from sbs_utils.procedural.links import link, unlink
#from sbs_utils.procedural.query import get_role_string
from sbs_utils.procedural.roles import remove_role, get_role_string

from data.missions.common.library_function_patches import ensure_on_gui_task, gui_patched, gui_switch_to

from controller_game_setup_data import get_game_setup_data

def jump_into_game(delay_reroute_workaround=False):
    client_id = get_variable("client_id")
    GAME_SETUP_DATA = get_game_setup_data() # pylint: disable=invalid-name
    
    # TODO when crew name gets added
    # Though these should probably be synced while they're being edited
    # instead of here. Which I think would fix
    # https://github.com/artemis-sbs/LegendaryMissions/issues/82
    #sbs.set_client_string(client_id, "crew_name", crew_name)
    #set_inventory_value(client_id, "CREW_NAME", crew_name)
    
    # TODO old code which was in common_console_select.mast
    # Is it really needed? Or can it be moved somewhere else?
    sbs.set_beam_damages(client_id, 7.0, GAME_SETUP_DATA.difficulty)
    
    # I should probably just ignore the console_previous field entirely
    # Making it support multiple consoles would be ick w/o being able
    # to await inside python functions
    #sbs.set_client_string(client_id, "console_previous", CONSOLE_SELECT)
    
    first_console_label = GAME_SETUP_DATA.get_all_console_slots_selected_by_client(client_id)[0].label
    
    gui_switch_to(first_console_label, delay_reroute_workaround=delay_reroute_workaround)
