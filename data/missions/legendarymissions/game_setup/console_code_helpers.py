import sbs

from sbs_utils.helpers import FrameContext
from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import get_variable
from sbs_utils.procedural.gui.console import gui_console
from sbs_utils.procedural.gui.console_types import gui_get_console_type
from sbs_utils.procedural.inventory import set_inventory_value
from sbs_utils.procedural.links import link, unlink

from data.missions.common.library_function_patches import ensure_on_gui_task
from data.missions.common.gui_top_tabs import is_gui_top_tabs_enabled, gui_create_top_tabs, GuiTopTab, gui_top_tab_help_key, gui_top_tab_library_key, gui_top_tab_upgrades_key

from controller_game_setup_data import get_game_setup_data
from gui_help_button import create_help_button
from gui_library_button import create_library_button

@label()
def prepare_console(console_identifier, rerun_label=None, widget_list=None, enable_helm_jump_drive_controls=False):
    """
    
    Returns:
        True if the current task should continue
        False if the current task should ->END
    """
    GAME_SETUP_DATA = get_game_setup_data()
    client_id = get_variable("client_id")
    game_setup_assigned_ship = GAME_SETUP_DATA.get_selected_ship(client_id)
    
    if rerun_label is None:
        rerun_label = gui_get_console_type(console_identifier).label
    if not ensure_on_gui_task(rerun_label):
        return False
    
    all_top_tabs = [GuiTopTab(console_slot.identifier, console_slot.display_name, console_slot.label) for console_slot in GAME_SETUP_DATA.get_all_console_slots_selected_by_client(client_id)]
    if game_setup_assigned_ship is not None and game_setup_assigned_ship.is_at_least_one_console_selected_by_client(client_id):
        all_top_tabs.append(GuiTopTab(gui_top_tab_upgrades_key(), "Upgrades", "upgrade_screen"))
    gui_create_top_tabs(console_identifier, all_top_tabs, x_right="100-72px")
    if is_gui_top_tabs_enabled(client_id):
        create_library_button(rerun_label, section_style="area:100-72px,0,100-36px,36px;")
        create_help_button(rerun_label)
    
    # Sometimes consoles change the engine's client-ship assignments
    # (e.g. gamemaster, flight hangar)
    # So always reset the engine's assignment to the player ship picked in console selection
    if game_setup_assigned_ship is not None:
        engine_assigned_ship_id = sbs.get_ship_of_client(client_id)
        if engine_assigned_ship_id != game_setup_assigned_ship.spawned_ship_id:
            sbs.assign_client_to_ship(client_id, game_setup_assigned_ship.spawned_ship_id)
            unlink(engine_assigned_ship_id, "consoles", client_id)
        link(game_setup_assigned_ship.spawned_ship_id, "consoles", client_id)
    
    # This is read from in the upgrade tab and some gamemaster comms stuff
    # I believe it should be set to the currently-open screen on the client
    set_inventory_value(client_id, "CONSOLE_TYPE", console_identifier)
    
    if widget_list is not None:
        FrameContext.page.set_widget_list(console_identifier, widget_list)
    else:
        gui_console(console_identifier, enable_helm_jump_drive_controls)
    
    return True
