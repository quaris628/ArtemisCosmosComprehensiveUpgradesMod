from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import END, get_variable, set_variable
from sbs_utils.procedural.gui import gui_icon_button, gui_message, gui_section

from data.missions.common.library_function_patches import gui_switch_to
from data.missions.common.gui_color_scheme import color_text

from data.missions.legendarymissions.documents.document_screen import set_document_back_button_label

from controller_game_setup_data import get_game_setup_data

# ----- creation -----

def create_library_button(back_label, section_style="area:100-36px,0,100,36px;"):
    gui_section(style=section_style)
    library_button = gui_icon_button(f"icon_index:0;color:{color_text()};")
    
    gui_message(library_button, _open_library_document)
    
    _set_library_button_back_label(back_label)

@label()
def _open_library_document():
    client_id = get_variable("client_id")
    GAME_SETUP_DATA = get_game_setup_data()
    
    set_document_back_button_label(_get_library_button_back_label())
    gui_switch_to("gui_library_document_main", delay_reroute_workaround=True)
    
    yield END()

# ----- setter/getter wrappers -----

def _get_library_button_back_label():
    return get_variable(_LIBRARY_BUTTON_BACK_LABEL_VAR_NAME)

def _set_library_button_back_label(back_label):
    set_variable(_LIBRARY_BUTTON_BACK_LABEL_VAR_NAME, back_label)

_LIBRARY_BUTTON_BACK_LABEL_VAR_NAME = "_library_button_back_label"
