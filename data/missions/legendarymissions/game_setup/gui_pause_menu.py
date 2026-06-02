import sbs

from sbs_utils.fs import get_mission_name, get_startup_mission_name
from sbs_utils.helpers import FrameContext
from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import AWAIT, END, jump, get_variable, set_variable, task_schedule
from sbs_utils.procedural.gui import gui_button, gui_hide, gui_message, gui_row, gui_section, gui_show, gui_text
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.links import link
from sbs_utils.procedural.maps import map_get_properties
from sbs_utils.procedural.query import to_space_object
from sbs_utils.procedural.signal import signal_emit, signal_register
from sbs_utils.procedural.timers import delay_app, delay_sim

from data.missions.common.library_function_patches import gui_represent_patched
from data.missions.common.controller_game_statistics import get_game_statistics
from data.missions.common.gui_color_scheme import color_background, color_text
from data.missions.common.operator_mode import is_operator_mode_enabled

from background_skybox_hack import create_skybox_background_on_client
from game_state import end_game, get_game_state, game_state_paused, is_game_in_progress, resume_game, signal_game_ended, signal_game_state_changed, signal_game_started

# ----- creation -----

def create_pause_menu(client_id):
    current_mission_name = get_mission_name()
    startup_mission_name = get_startup_mission_name()
    
    # Force static png b/c while paused the animation won't run anyway
    background_image = create_skybox_background_on_client(client_id, force_fallback_to_static_png=True, skip_fake_options_button=True)
    
    # ----- main section -----
    
    main_section = gui_section(style=f"area:5,50-160px,95,50+160px;background:{color_background()};")
    
    title_text = gui_text("Simulation is Paused", style=f"font:gui-6;justify:center;color:{color_text()};")
    
    if client_id == 0 and is_operator_mode_enabled():
        _set_pause_menu_gui_elements(main_section, title_text, None, None, None, None, None, None, None, None, background_image)
        _set_confirm_label(None)
        task_schedule(_pause_menu_sync_hide_or_show_after_delay)
        return
    
    gui_row(style="row-height:64px;")
    resume_button = gui_button("Resume Game", style=f"font:gui-3;padding:10px,5px,10px,5px;color:{color_text()}")
    
    gui_row(style="row-height:64px;")
    end_button = gui_button("End Game", style=f"font:gui-3;padding:10px,5px,10px,5px;color:{color_text()}")
    
    if current_mission_name is not None and len(current_mission_name) > 0:
        gui_row(style="row-height:64px;")
        restart_current_mission_button = gui_button(f"Reboot Scripts for {current_mission_name}", style=f"font:gui-3;padding:10px,5px,10px,5px;color:{color_text()};")
    else:
        restart_current_mission_button = None
    
    if startup_mission_name is not None and len(startup_mission_name) > 0 and current_mission_name != startup_mission_name:
        gui_row(style="row-height:64px;")
        back_to_startup_mission_button = gui_button(f"Back to {startup_mission_name}", style=f"font:gui-3;padding:10px,5px,10px,5px;color:{color_text()};")
    else:
        back_to_startup_mission_button = None
    
    # ----- confirmation buttons -----
    
    confirm_section = gui_section(style=f"area:5,50+160px,95,50+320px;background:{color_background()};")
    
    confirm_message_text = gui_text("", style=f"font:gui-2;padding:10px,5px,10px,5px;color:{color_text()};")
    
    gui_row(style="row-height:72px;")
    cancel_button = gui_button("Cancel", style=f"font:gui-3;padding:10px,5px,5,5px;color:{color_text()};")
    confirm_button = gui_button("", style=f"font:gui-3;padding:5px,5px,10px,5px;color:{color_text()};")
    
    _set_pause_menu_gui_elements(main_section, title_text, resume_button, end_button, restart_current_mission_button, back_to_startup_mission_button, confirm_section, confirm_message_text, cancel_button, confirm_button, background_image)
    _set_confirm_label(None)
    
    # TODO listening to game state changes might be buggy
    # Only the `on change GAME_STATE` seemed to work before
    #signal_register(signal_game_state_changed(), _pause_menu_on_game_state_changed, is_temporary=True)
    gui_message(resume_button, _pause_menu_on_resume_button_clicked)
    gui_message(end_button, _pause_menu_on_end_game_button_clicked)
    if restart_current_mission_button is not None:
        gui_message(restart_current_mission_button, _pause_menu_on_restart_current_mission_button_clicked)
    if back_to_startup_mission_button is not None:
        gui_message(back_to_startup_mission_button, _pause_menu_on_back_to_startup_mission_button_clicked)
    gui_message(cancel_button, _pause_menu_on_cancel_button_clicked)
    gui_message(confirm_button, _pause_menu_on_confirm_button_clicked)
    
    task_schedule(_pause_menu_sync_hide_or_show_after_delay)

@label()
def _pause_menu_sync_hide_or_show_after_delay():
    yield AWAIT(delay_app(0))
    yield jump(_pause_menu_sync_hide_or_show)

# ----- showing/hiding -----

@label()
def _pause_menu_sync_hide_or_show():
    client_id = get_variable("client_id")
    main_section, title_text, resume_button, end_button, restart_current_mission_button, back_to_startup_mission_button, confirm_section, confirm_message_text, cancel_button, confirm_button, background_image = _get_pause_menu_gui_elements()
    
    if get_game_state() == game_state_paused():
        gui_show(background_image)
        main_section.background_color = color_background()
        gui_show(title_text)
        if not(client_id == 0 and is_operator_mode_enabled()):
            gui_show(resume_button)
            gui_show(end_button)
            if restart_current_mission_button is not None:
                gui_show(restart_current_mission_button)
            if back_to_startup_mission_button is not None:
                gui_show(back_to_startup_mission_button)
    else:
        gui_hide(background_image)
        main_section.background_color = "#00000000"
        gui_hide(title_text)
        if not(client_id == 0 and is_operator_mode_enabled()):
            gui_hide(resume_button)
            gui_hide(end_button)
            if restart_current_mission_button is not None:
                gui_hide(restart_current_mission_button)
            if back_to_startup_mission_button is not None:
                gui_hide(back_to_startup_mission_button)
    gui_represent_patched(background_image)
    gui_represent_patched(main_section)
    gui_represent_patched(title_text)
    if not(client_id == 0 and is_operator_mode_enabled()):
        gui_represent_patched(resume_button)
        gui_represent_patched(end_button)
        if restart_current_mission_button is not None:
            gui_represent_patched(restart_current_mission_button)
        if back_to_startup_mission_button is not None:
            gui_represent_patched(back_to_startup_mission_button)
        
        confirm_section.background_color = "#00000000"
        gui_hide(confirm_message_text)
        gui_hide(cancel_button)
        gui_hide(confirm_button)
        gui_represent_patched(confirm_section)
        gui_represent_patched(confirm_message_text)
        gui_represent_patched(cancel_button)
        gui_represent_patched(confirm_button)
        _set_confirm_label(None)
    
    yield END()

def _pause_menu_show_confirm_section(message, confirm_button_label, confirm_label):
    main_section, title_text, resume_button, end_button, restart_current_mission_button, back_to_startup_mission_button, confirm_section, confirm_message_text, cancel_button, confirm_button, background_image = _get_pause_menu_gui_elements()
    
    confirm_message_text.value = message
    confirm_button.value = confirm_button_label
    confirm_section.background_color = color_background()
    
    gui_show(confirm_message_text)
    gui_show(cancel_button)
    gui_show(confirm_button)
    gui_represent_patched(confirm_section)
    gui_represent_patched(confirm_message_text)
    gui_represent_patched(cancel_button)
    gui_represent_patched(confirm_button)
    
    _set_confirm_label(confirm_label)

def _pause_menu_hide_confirm_section():
    main_section, title_text, resume_button, end_button, restart_current_mission_button, back_to_startup_mission_button, confirm_section, confirm_message_text, cancel_button, confirm_button, background_image = _get_pause_menu_gui_elements()
    
    confirm_message_text.value = ""
    confirm_button.value = ""
    confirm_section.background_color = "#00000000"
    
    gui_hide(confirm_message_text)
    gui_hide(cancel_button)
    gui_hide(confirm_button)
    gui_represent_patched(confirm_section)
    gui_represent_patched(confirm_message_text)
    gui_represent_patched(cancel_button)
    gui_represent_patched(confirm_button)
    
    _set_confirm_label(None)

# ----- on-events -----

@label()
def _pause_menu_on_game_state_changed():
    yield jump(_pause_menu_sync_hide_or_show)

@label()
def _pause_menu_on_resume_button_clicked():
    
    resume_game()
    
    yield END()

@label()
def _pause_menu_on_end_game_button_clicked():
    
    _pause_menu_show_confirm_section("Are you sure you want to end the current game?", "Confirm End Game", _pause_menu_on_confirm_end_game)
    
    yield END()

@label()
def _pause_menu_on_confirm_end_game():
    main_section, title_text, resume_button, end_button, restart_current_mission_button, back_to_startup_mission_button, confirm_section, confirm_message_text, cancel_button, confirm_button, background_image = _get_pause_menu_gui_elements()
    
    GAME_STATISTICS = get_game_statistics()
    GAME_STATISTICS.record_game_end(reason="the simulation was stopped.", is_success=True)
    end_game()
    
    yield END()

@label()
def _pause_menu_on_restart_current_mission_button_clicked():
    current_mission_name = get_mission_name()
    
    _pause_menu_show_confirm_section(f"Are you sure you want to reboot the scripts for {current_mission_name}?\nDoing so will end the current game and reset the simulation setup settings to their defaults.", f"Confirm Reboot Scripts for {current_mission_name}", _pause_menu_on_confirm_restart_current_mission)
    
    yield END()

@label()
def _pause_menu_on_confirm_restart_current_mission():
    
    # TODO: clear guis and show message that the game is restarting (like a loading screen)
    # And share this code between this restart button and the one on the game setup screen
    # (in gui_game_setup.mast)
    sbs.run_next_mission(get_mission_name())
    
    yield END()

@label()
def _pause_menu_on_back_to_startup_mission_button_clicked():
    startup_mission_name = get_startup_mission_name()
    
    _pause_menu_show_confirm_section(f"Are you sure you want to go back to {startup_mission_name}?\nDoing so will end the current game and reset the simulation setup settings to their defaults.", f"Confirm Go Back to {startup_mission_name}", _pause_menu_on_confirm_back_to_startup_mission)
    
    yield END()

@label()
def _pause_menu_on_confirm_back_to_startup_mission():
    
    sbs.run_next_mission(get_startup_mission_name())
    
    yield END()

@label()
def _pause_menu_on_cancel_button_clicked():
    
    _pause_menu_hide_confirm_section()
    
    yield END()

@label()
def _pause_menu_on_confirm_button_clicked():
    yield jump(_get_confirm_label())

# ----- setter/getter wrappers -----

def _get_pause_menu_gui_elements():
    elements = get_variable(_PAUSE_MENU_GUI_ELEMENTS_VAR_NAME)
    return elements[0], elements[1], elements[2], elements[3], elements[4], elements[5], elements[6], elements[7], elements[8], elements[9], elements[10]

def _set_pause_menu_gui_elements(main_section, title_text, resume_button, end_button, restart_current_mission_button, back_to_startup_mission_button, confirm_section, confirm_message_text, cancel_button, confirm_button, background_image):
    set_variable(_PAUSE_MENU_GUI_ELEMENTS_VAR_NAME, (main_section, title_text, resume_button, end_button, restart_current_mission_button, back_to_startup_mission_button, confirm_section, confirm_message_text, cancel_button, confirm_button, background_image))

_PAUSE_MENU_GUI_ELEMENTS_VAR_NAME = "_pause_menu_gui_elements_var_name"

def _get_confirm_label():
    return get_variable(_PAUSE_MENU_CONFIRM_LABEL_VAR_NAME)

def _set_confirm_label(confirm_label):
    set_variable(_PAUSE_MENU_CONFIRM_LABEL_VAR_NAME, confirm_label)

_PAUSE_MENU_CONFIRM_LABEL_VAR_NAME = "_pause_menu_confirm_label_var_name"

# ----- signals -----

def signal_pause_menu_restart_current_mission_clicked():
    return "pause_menu_restart_current_mission_clicked"

def signal_pause_menu_back_to_default_mission_clicked():
    return "pause_menu_back_to_default_mission_clicked"
