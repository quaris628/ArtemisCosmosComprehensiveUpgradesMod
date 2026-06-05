from dataclasses import dataclass

from sbs_utils.gui import get_client_aspect_ratio
from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import AWAIT, END, get_variable, set_variable
from sbs_utils.procedural.gui import gui_checkbox, gui_hide, gui_message, gui_section
from sbs_utils.procedural.signal import signal_emit, signal_register
from sbs_utils.procedural.timers import delay_app

from data.missions.common.library_function_patches import gui_represent_patched, gui_switch_to
from data.missions.common.gui_color_scheme import color_text

def gui_create_top_tabs(current_tab_key, top_tabs_iterable, x_left_px=200, y_top_px=0, x_right="100", force_show_all_text=False):
    client_id = get_variable("client_id")
    
    if not is_gui_top_tabs_enabled(client_id):
        return
    
    if not force_show_all_text:
        # If the text of a checkbox's label is too long to fit inside the checkbox,
        # then it will spill onto the "next line" even if that "next line" is outside
        # of the checkbox. And unfortunately, as far as I know, there's no simple way
        # to make it truncate the text.
        # So instead, manually truncate the tab's label by calculating how many
        # characters of the display name can fit within the width of the checkbox.
        width_of_entire_window = get_client_aspect_ratio(client_id).x
        # options button is ~200px wide
        width_for_all_tabs = width_of_entire_window - x_left_px
        width_for_one_tab = width_for_all_tabs / len(top_tabs_iterable)
        # checkbox bulb is ~30px wide
        width_for_one_tabs_text = width_for_one_tab - 30
        # capital letters are ~20px wide, and lowercase are ~16px wide
        # (there are some exceptions, e.g. lowercase m is ~24px wide)
        length_to_trim_display_name = int((width_for_one_tabs_text) / 20)
    else:
        length_to_trim_display_name = None
    
    # It would've been nice to use gui_radio for this,
    # but it seemed like its color and text is not customizeable.
    # TODO write a feature request?
    gui_section(style=f"area:{x_left_px}px,{y_top_px}px,{x_right},{y_top_px+36}px;")
    for top_tab in top_tabs_iterable:
        _create_single_top_tab(top_tab, length_to_trim_display_name)
    
    current_selection_checkbox = _get_top_tab_checkbox(current_tab_key)
    current_selection_checkbox.value = True
    _set_gui_top_tabs_current_selection_key(current_tab_key)

def _create_single_top_tab(top_tab, length_to_trim_display_name):
    display_name = top_tab.display_name
    if length_to_trim_display_name is not None:
        display_name = display_name[:length_to_trim_display_name]
    checkbox = gui_checkbox(display_name, style=f"font:gui-3;color:{color_text()};", data={"TOP_TAB": top_tab})
    gui_message(checkbox, label=_on_top_tab_clicked)
    _add_to_top_tabs_gui_elements(top_tab.key, checkbox)

def gui_remove_top_tabs(tab_keys_to_remove=None, delay_reroute_workaround=False):
    top_tab_keys_to_checkboxes = _get_top_tab_keys_to_checkboxes_dict()
    if tab_keys_to_remove is None:
        # Remove all
        tab_keys_to_remove = top_tab_keys_to_checkboxes.keys()
    
    # Hide everything first...
    for tab_key in tab_keys_to_remove:
        checkbox = top_tab_keys_to_checkboxes[tab_key]
        gui_hide(checkbox)
    # ...so that when these represents happen,
    # all gaps left by now-hidden tabs will be filled
    for tab_key, checkbox in top_tab_keys_to_checkboxes.items():
        gui_represent_patched(checkbox)
    
    current_selection_key = _get_gui_top_tabs_current_selection_key()
    if current_selection_key in tab_keys_to_remove:
        # Switch to a different tab, if one exists
        if 0 < len(top_tab_keys_to_checkboxes) - len(tab_keys_to_remove):
            new_top_tab = None
            for tab_key, checkbox in top_tab_keys_to_checkboxes.items():
                if tab_key not in tab_keys_to_remove:
                    new_top_tab = checkbox.data["TOP_TAB"]
                    break
            if new_top_tab is not None:
                gui_switch_to(new_top_tab.gui_main_label, delay_reroute_workaround=delay_reroute_workaround)
        # if zero tabs exist now, then switch to console selection
        # (As far as I know, no situation can trigger this code path currently)
        else:
            gui_switch_to("gui_console_selection_main", delay_reroute_workaround=delay_reroute_workaround)

@label()
def _on_top_tab_clicked():
    top_tab = get_variable("TOP_TAB")
    
    current_selection_key = _get_gui_top_tabs_current_selection_key()
    if current_selection_key == top_tab.key:
        checkbox = _get_top_tab_checkbox(current_selection_key)
        checkbox.value = True
        gui_represent_patched(checkbox)
        yield END()
    
    gui_switch_to(top_tab.gui_main_label, delay_reroute_workaround=True)
    yield END()

@dataclass(eq=False, frozen=True)
class GuiTopTab:
    key: str
    display_name: str
    gui_main_label: str

# ----- special top tab keys (constants) -----

def gui_top_tab_upgrades_key():
    return "upgrades"

def gui_top_tab_library_key():
    # must match 'document_type = "Library"' in library_tab.mast
    return "Library"

def gui_top_tab_help_key():
    # must match 'document_type = "help"' in help_tab.mast
    return "help"

# ----- signals -----

def signal_gui_top_tab_clicked(client_id):
    return f"gui_top_tab_clicked_{client_id}"

# ----- setter/getter wrappers -----

# top tabs gui elements

def _get_top_tab_keys_to_checkboxes_dict():
    return get_variable(_GUI_TOP_TABS_GUI_ELEMENTS_VAR_NAME)

def _get_top_tab_checkbox(key):
    all_gui_elements = get_variable(_GUI_TOP_TABS_GUI_ELEMENTS_VAR_NAME)
    if all_gui_elements is None or key not in all_gui_elements:
        return None
    return all_gui_elements[key]

def _add_to_top_tabs_gui_elements(key, checkbox):
    all_gui_elements = get_variable(_GUI_TOP_TABS_GUI_ELEMENTS_VAR_NAME)
    if all_gui_elements is None:
        all_gui_elements = {}
    all_gui_elements[key] = checkbox
    set_variable(_GUI_TOP_TABS_GUI_ELEMENTS_VAR_NAME, all_gui_elements)

_GUI_TOP_TABS_GUI_ELEMENTS_VAR_NAME = "_gui_top_tabs_gui_elements"

# currently-selected top tab

def _get_gui_top_tabs_current_selection_key():
    return get_variable(_GUI_TOP_TABS_CURRENT_SELECTION_VAR_NAME)

def _set_gui_top_tabs_current_selection_key(key):
    set_variable(_GUI_TOP_TABS_CURRENT_SELECTION_VAR_NAME, key)

_GUI_TOP_TABS_CURRENT_SELECTION_VAR_NAME = "_gui_top_tabs_current_selection_var_name"

# enable/disable top tabs

# Does not remove any already-existing top tabs.
# Just prevents new ones from being added.
def disable_gui_top_tabs(client_id):
    disabled_on_clients_set = get_variable(_GUI_TOP_TABS_DISABLED_ON_CLIENTS_VAR_NAME)
    if disabled_on_clients_set is None:
        disabled_on_clients_set = set()
    disabled_on_clients_set.add(client_id)
    set_variable(_GUI_TOP_TABS_DISABLED_ON_CLIENTS_VAR_NAME, disabled_on_clients_set)

# Does not make any already-set-up top tabs start showing.
# Just allows new ones to be created.
def enable_gui_top_tabs(client_id):
    disabled_on_clients_set = get_variable(_GUI_TOP_TABS_DISABLED_ON_CLIENTS_VAR_NAME)
    if disabled_on_clients_set is None:
        disabled_on_clients_set = set()
    disabled_on_clients_set.discard(client_id)
    set_variable(_GUI_TOP_TABS_DISABLED_ON_CLIENTS_VAR_NAME, disabled_on_clients_set)

def is_gui_top_tabs_enabled(client_id):
    disabled_on_clients_set = get_variable(_GUI_TOP_TABS_DISABLED_ON_CLIENTS_VAR_NAME)
    if disabled_on_clients_set is None:
        return True
    return client_id not in disabled_on_clients_set

_GUI_TOP_TABS_DISABLED_ON_CLIENTS_VAR_NAME = "_gui_top_tabs_disabled_on_clients"
