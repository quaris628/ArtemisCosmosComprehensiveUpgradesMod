from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import END, get_variable, set_variable
from sbs_utils.procedural.gui import gui_icon_button, gui_message, gui_section, gui_text

from data.missions.common.library_function_patches import gui_switch_to
from data.missions.common.gui_color_scheme import color_text

from data.missions.legendarymissions.documents.document_screen import set_document_back_button_label

from controller_game_setup_data import get_game_setup_data

# ----- creation -----

def create_help_button(back_label, section_style="area:100-36px,0,100,36px;", unready_on_click=False):
    gui_section(style=section_style)
    help_button = gui_icon_button(f"icon_index:129;color:{color_text()};")
    gui_section(style=section_style)
    gui_text("?", style=f"font:gui-3;justify:center;color:{color_text()};")
    
    _set_help_button_back_label(back_label)
    _set_help_button_unready_on_click(unready_on_click)
    gui_message(help_button, _open_help_document)

@label()
def _open_help_document():
    client_id = get_variable("client_id")
    GAME_SETUP_DATA = get_game_setup_data()
    
    if _get_help_button_unready_on_click():
        GAME_SETUP_DATA.client_unready(client_id)
    set_document_back_button_label(_get_help_button_back_label())
    gui_switch_to("gui_help_document_main", delay_reroute_workaround=True)
    
    # TODO what if the ship gets destroyed? switch to game end from document page
    
    yield END()

# ----- setter/getter wrappers -----

def _get_help_button_back_label():
    return get_variable(_HELP_BUTTON_BACK_LABEL_VAR_NAME)

def _set_help_button_back_label(back_label):
    set_variable(_HELP_BUTTON_BACK_LABEL_VAR_NAME, back_label)

_HELP_BUTTON_BACK_LABEL_VAR_NAME = "_help_button_back_label"

def _get_help_button_unready_on_click():
    return get_variable(_HELP_BUTTON_UNREADY_ON_CLICK_VAR_NAME)

def _set_help_button_unready_on_click(unready_on_click):
    set_variable(_HELP_BUTTON_UNREADY_ON_CLICK_VAR_NAME, unready_on_click)

_HELP_BUTTON_UNREADY_ON_CLICK_VAR_NAME = "_help_button_unready_on_click"
