
from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import END, AWAIT, jump, get_variable, set_variable, task_schedule
from sbs_utils.procedural.signal import signal_register
from sbs_utils.procedural.gui import gui_section, gui_text, gui_message, gui_ship, gui_row, gui_show, gui_hide
from sbs_utils.procedural.timers import delay_app

from data.missions.common.library_function_patches import gui_represent_patched, gui_dropdown_patched
from data.missions.common.model_single_seat_craft_type import CraftCategory
from data.missions.common.controller_vessel_types_data import get_vessel_types_data
from data.missions.common.gui_color_scheme import color_text, color_text_secondary, color_background, color_divider, color_divider_secondary

def create_label_value_pair(label_display_string, value_display_string, text_color=None):
    if text_color is None:
        text_color = color_text()
    gui_row(style="row-height:32px;padding:0,4px,8px,0;")
    gui_text(label_display_string, style=f"font:gui-3;justify:right;color:{text_color};")
    gui_text(value_display_string, style=f"font:gui-3;justify:right;col-width:64px;color:{text_color};")
