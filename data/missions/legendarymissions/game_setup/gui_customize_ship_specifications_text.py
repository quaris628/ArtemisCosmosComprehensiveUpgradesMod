from random import randrange

from sbs_utils.mast.label import label
from sbs_utils.procedural.execution import END, AWAIT, jump, get_variable, set_variable, task_schedule
from sbs_utils.procedural.signal import signal_register
from sbs_utils.procedural.gui import gui_section, gui_sub_section, gui_text, gui_message, gui_ship, gui_row, gui_show, gui_hide
from sbs_utils.procedural.timers import delay_app

from data.missions.common.library_function_patches import gui_represent_patched, gui_dropdown_patched
from data.missions.common.model_single_seat_craft_type import CraftCategory
from data.missions.common.controller_vessel_types_data import get_vessel_types_data
from data.missions.common.gui_color_scheme import color_text, color_text_secondary, color_background, color_divider, color_divider_secondary

from model_player_ship_setup_data import signal_player_ship_setup_data_ship_type_changed
from controller_game_setup_data import get_game_setup_data

# ----- creation -----

def create_ship_type_specifications_text(ship, x_left, y_top, x_right, y_bottom):
    VESSEL_TYPES_DATA = get_vessel_types_data()
    ship_type = VESSEL_TYPES_DATA.get_ship_type_from_key(ship.ship_type_key)
    beam_details_label_strings = _get_beam_details_label_strings()
    ordinance_type_label_strings = _get_ordinance_type_label_strings()
    
    # ----- start gui arrangement code -----
    
    gui_section(style=f"area:{x_left},{y_top},{x_right},{y_bottom};background:{color_background()};")
    
    _create_header("Weapons")
    
    # ----- Beams -----
    
    beam_count_text = _create_big_value()
    
    gui_row(style=f"row-height:{24*len(beam_details_label_strings)}px;")
    
    # Column of labels
    all_beam_details_label_texts = []
    # The "with" syntax is necessary
    # https://github.com/orgs/artemis-sbs/discussions/586#discussioncomment-16688356
    with gui_sub_section(style="col-width:135px;"):
        for label_string in beam_details_label_strings:
            gui_row(style="row-height:24px;")
            beam_details_label_text = gui_text(label_string, style=f"font:gui-2;justify:right;padding:0,0,5px,0;color:{color_text_secondary()};")
            all_beam_details_label_texts.append(beam_details_label_text)
    
    # Table of values
    beam_texts_list = []
    for i in range(_MAXIMUM_DISPLAYABLE_BEAM_DETAILS_COUNT):
        # The "with" syntax is necessary
        # https://github.com/orgs/artemis-sbs/discussions/586#discussioncomment-16688356
        with gui_sub_section(style="col-width:48px;"):
            beam_texts = []
            for i in range(len(beam_details_label_strings)):
                gui_row(style="row-height:24px;")
                beam_field_text = gui_text("?", style=f"font:gui-2;justify:left;color:{color_text()};")
                beam_texts.append(beam_field_text)
            beam_texts_list.append(beam_texts)
    
    # ----- Torpedoes -----
    
    all_magazine_label_texts = []
    ordinance_type_max_texts = []
    
    tubes_count_text = _create_big_value()
    
    gui_row(style="row-height:24px;")
    # Work around being normally-unable to display colons with the $text: syntax
    # https://github.com/artemis-sbs/LegendaryMissions/issues/566#issuecomment-4291760757
    magazine_label_text = gui_text("$text:Magazine Capacity:;font:gui-2;justify:center;color:{color_text_secondary()};")
    all_magazine_label_texts.append(magazine_label_text)
    
    # Column of label-value pairs
    gui_row(style=f"row-height:{24*len(ordinance_type_label_strings)}px;")
    with gui_sub_section():
        for label_string in ordinance_type_label_strings:
            ordinance_type_max_value_text, ordinance_type_max_label_text = _create_label_value_pair(label_string)
            all_magazine_label_texts.append(ordinance_type_max_label_text)
            ordinance_type_max_texts.append(ordinance_type_max_value_text)
    
    # ----- Engines -----
    
    _create_header("Engines")
    drive_text = _create_big_value()
    drive_energy_cost_text, ignored_var = _create_label_value_pair("Drive Energy Draw")
    speed_text, ignored_var = _create_label_value_pair("Speed*")
    turn_rate_text, ignored_var = _create_label_value_pair("Turn Rate*")
    
    # ----- Misc -----
    
    _create_header("Miscellaneous")
    shuttles_text, ignored_var = _create_label_value_pair("Shuttles")
    fighters_text, ignored_var = _create_label_value_pair("Fighters")
    bombers_text, ignored_var = _create_label_value_pair("Bombers")
    ship_energy_cost_text, ignored_var = _create_label_value_pair("Overall Energy Draw")
    sensor_strength_text, ignored_var = _create_label_value_pair("Sensor strength*")
    
    # ----- footnote -----
    
    gui_section(style=f"area:{x_left}+10px,{y_bottom}-24px,{x_right},{y_bottom};")
    gui_text("* Varies with engineering power.", style=f"font:gui-2;justify:left;color:{color_text_secondary()};")
    
    # ----- end gui arrangement code -----
    
    _set_ship_type_specifications_gui_elements(beam_count_text, all_beam_details_label_texts, beam_texts_list, tubes_count_text, all_magazine_label_texts, ordinance_type_max_texts, drive_text, drive_energy_cost_text, speed_text, turn_rate_text, shuttles_text, fighters_text, bombers_text, sensor_strength_text, ship_energy_cost_text)
    
    signal_register(signal_player_ship_setup_data_ship_type_changed(ship.number), _update_ship_type_specifications_after_delay, is_temporary=True)
    
    task_schedule(_update_ship_type_specifications_after_delay, data={"SHIP": ship})

@label()
def _update_ship_type_specifications_after_delay():
    # If an element is hidden prior to it being presented for the first time,
    # then it will never show again.
    # https://github.com/artemis-sbs/LegendaryMissions/issues/513#issuecomment-3931007180
    # So work around this by adding a short delay before hiding the element,
    # so that the element will (hopefully) have been presented already by the
    # time gui_hide is called.
    yield AWAIT(delay_app(0))
    
    yield jump(_sync_ship_type_specifications_on_ship_type_changed)

def _create_header(title_display_string):
    gui_row(style="row-height:30px;")
    gui_text(title_display_string, style=f"font:gui-3;justify:left;padding:10px,0;color:{color_text_secondary()};")
    gui_row(style=f"row-height:2px;background:{color_divider_secondary()};padding:0,0,5px,0;")
    gui_text("")

def _create_big_value():
    gui_row(style="row-height:28px;")
    value_text = gui_text("?", style=f"font:gui-3;justify:center;color:{color_text()};")
    return value_text

def _create_label_value_pair(label_display_string):
    gui_row(style="row-height:24px;")
    label_text = gui_text(label_display_string, style=f"font:gui-2;justify:right;col-width:160px;color:{color_text_secondary()};")
    value_text = gui_text("?", style=f"font:gui-2;padding:10px,0;color:{color_text()};")
    return value_text, label_text

# ----- syncing -----

@label()
def _sync_ship_type_specifications_on_ship_type_changed():
    VESSEL_TYPES_DATA = get_vessel_types_data()
    ship = get_variable("SHIP")
    ship_type = VESSEL_TYPES_DATA.get_ship_type_from_key(ship.ship_type_key)
    beam_count_text, all_beam_details_label_texts, beam_texts_list, tubes_count_text, all_magazine_label_texts, ordinance_type_max_texts, drive_text, drive_energy_cost_text, speed_text, turn_rate_text, shuttles_text, fighters_text, bombers_text, sensor_strength_text, ship_energy_cost_text = _get_ship_type_specifications_gui_elements()
    
    # Beams
    
    if len(ship_type.beams) == 0:
        beam_count_text.value = "No Beams"
        gui_represent_patched(beam_count_text)
        for text in all_beam_details_label_texts:
            gui_hide(text)
            gui_represent_patched(text)
        for texts in beam_texts_list:
            for text in texts:
                gui_hide(text)
                gui_represent_patched(text)
    else:
        beam_count_text.value = f"{len(ship_type.beams)} Beam{'' if len(ship_type.beams) == 1 else 's'}"
        gui_represent_patched(beam_count_text)
        for text in all_beam_details_label_texts:
            gui_show(text)
            gui_represent_patched(text)
        for i in range(min(len(ship_type.beams), _MAXIMUM_DISPLAYABLE_BEAM_DETAILS_COUNT)):
            beam = ship_type.beams[i]
            beam_texts = beam_texts_list[i]
            beam_texts[0].value = _get_beam_damage_display_string(beam.damage_coeff)
            beam_texts[1].value = _get_beam_cycle_time_display_string(beam.cycle_time)
            beam_texts[2].value = _get_beam_range_display_string(beam.range)
            beam_texts[3].value = _get_beam_barrel_angle_display_string(beam.barrel_angle)
            beam_texts[4].value = _get_beam_arc_width_display_string(beam.arcwidth)
            for j in range(5):
                gui_show(beam_texts[j])
                gui_represent_patched(beam_texts[j])
        
        for i in range(len(ship_type.beams), _MAXIMUM_DISPLAYABLE_BEAM_DETAILS_COUNT):
            beam_texts = beam_texts_list[i]
            for j in range(5):
                beam_texts[j].value = ""
                gui_show(beam_texts[j])
                gui_represent_patched(beam_texts[j])
    
    # Torpedoes
    
    if ship_type.tube_count == 0:
        tubes_count_text.value = "No Tubes"
        gui_represent_patched(tubes_count_text)
        for text in all_magazine_label_texts + ordinance_type_max_texts:
            gui_hide(text)
            gui_represent_patched(text)
    else:
        tubes_count_text.value = f"{ship_type.tube_count} Tube{'' if ship_type.tube_count == 1 else 's'}"
        gui_represent_patched(tubes_count_text)
        for magazine_label_text in all_magazine_label_texts:
            gui_show(magazine_label_text)
            gui_represent_patched(magazine_label_text)
        ordinance_type_label_strings = _get_ordinance_type_label_strings()
        for i in range(4):
            ordinance_type = ordinance_type_label_strings[i]
            ordinance_type_max_count = ship_type.max_ordinance_counts[ordinance_type]
            ordinance_type_max_texts[i].value = str(ordinance_type_max_count)
            gui_show(ordinance_type_max_texts[i])
            gui_represent_patched(ordinance_type_max_texts[i])
    
    # Engines
    
    if ship_type.has_warp_drive and ship_type.has_jump_drive:
        drive_text.value = "Hybrid Drive - Warp and Jump"
        drive_energy_cost_text.value = f"Warp {_get_efficiency_description(ship_type.warp_energy_cost)} ({ship_type.warp_energy_cost:.0%}), Jump {_get_efficiency_description(ship_type.jump_energy_cost)} ({ship_type.jump_energy_cost:.0%})"
    elif ship_type.has_warp_drive:
        drive_text.value = "Warp Drive"
        drive_energy_cost_text.value = f"{_get_efficiency_description(ship_type.warp_energy_cost)} ({ship_type.warp_energy_cost:.0%})"
    elif ship_type.has_jump_drive:
        drive_text.value = "Jump Drive"
        drive_energy_cost_text.value = f"{_get_efficiency_description(ship_type.jump_energy_cost)} ({ship_type.jump_energy_cost:.0%})"
    else:
        drive_text.value = "No FTL Drive - Impulse only"
        drive_energy_cost_text.value = "N/A"
    gui_represent_patched(drive_text)
    gui_represent_patched(drive_energy_cost_text)
    
    speed_text.value = f"{ship_type.speed_coeff:.1f}"
    gui_represent_patched(speed_text)
    
    turn_rate_text.value = f"{ship_type.turn_rate:.1f}"
    gui_represent_patched(turn_rate_text)
    
    # Single-seat craft
    
    shuttles_text.value = str(ship_type.single_seat_craft_counts[CraftCategory.SHUTTLE])
    fighters_text.value = str(ship_type.single_seat_craft_counts[CraftCategory.FIGHTER])
    bombers_text.value = str(ship_type.single_seat_craft_counts[CraftCategory.BOMBER])
    
    # Misc
    
    ship_energy_cost_text.value = f"{_get_efficiency_description(ship_type.ship_energy_cost)} ({ship_type.ship_energy_cost:.0%})"
    gui_represent_patched(ship_energy_cost_text)
    
    sensor_strength_text.value = f"{ship_type.scan_strength_coeff:.1f}"
    gui_represent_patched(sensor_strength_text)
    
    yield END()

# ----- beams -----

_MAXIMUM_DISPLAYABLE_BEAM_DETAILS_COUNT = 6

def _get_beam_details_label_strings():
    return ["Damage", "Shots/Minute*", "Range", "Relative Bearing", "Arc Width (deg)"]

def _get_beam_damage_display_string(damage_coeff):
    # Player beams' damage gets multiplied by 7 at
    # controller_game_setup_data.py > setup_game
    # sbs.set_beam_damages(0, 7.0, (GAME_SETUP_DATA.difficulty / 2.0) + 3.0)
    return _strip_trailing_zeroes(f"{damage_coeff * 7:.1f}")

def _get_beam_cycle_time_display_string(cycle_time):
    if cycle_time == 0:
        return "N/A"
    rounds_per_minute = 60 / cycle_time
    return _strip_trailing_zeroes(f"{rounds_per_minute:.1f}")

def _get_beam_range_display_string(beam_range):
    # TODO: convert to 11.1k format if 10k <= range
    return _strip_trailing_zeroes(f"{beam_range:.0f}")

def _get_beam_barrel_angle_display_string(barrel_angle):
    return _strip_trailing_zeroes(f"{barrel_angle:.0f}")

def _get_beam_arc_width_display_string(arc_width):
    return _strip_trailing_zeroes(f"{arc_width:.0f}")

# ----- torpedoes -----

def _get_ordinance_type_label_strings():
    return ["Homing", "Nuke", "EMP", "Mine"]

# ----- misc -----

def _get_efficiency_description(energy_cost):
    if energy_cost < 0.5:
        return "Extraordinarily efficient"
    elif energy_cost < 0.618:
        return "Very efficient"
    elif energy_cost < 0.8:
        return "Efficient"
    elif energy_cost < 1:
        return "Somewhat efficient"
    elif energy_cost == 1:
        return "Standard"
    elif energy_cost <= 1.25:
        return "Somewhat inefficient"
    elif energy_cost <= 1.618:
        return "Inefficient"
    elif energy_cost <= 2:
        return "Very inefficient"
    else:
        return "Extraordinarily inefficient"

def _strip_trailing_zeroes(float_string):
    if "." not in float_string:
        return float_string
    return float_string.rstrip("0").rstrip(".")

# ----- setter/getter wrappers -----

def _get_ship_type_specifications_gui_elements():
    elements = get_variable(_SHIP_TYPE_SPECIFICATIONS_GUI_ELEMENTS_VAR_NAME)
    return elements[0], elements[1], elements[2], elements[3], elements[4], elements[5], elements[6], elements[7], elements[8], elements[9], elements[10], elements[11], elements[12], elements[13], elements[14]

def _set_ship_type_specifications_gui_elements(beam_count_text, all_beam_details_label_texts, beam_texts_list, tubes_count_text, all_magazine_label_texts, ordinance_type_max_texts, drive_text, drive_energy_cost_text, speed_text, turn_rate_text, shuttles_text, fighters_text, bombers_text, sensor_strength_text, ship_energy_cost_text):
    elements = (beam_count_text, all_beam_details_label_texts, beam_texts_list, tubes_count_text, all_magazine_label_texts, ordinance_type_max_texts, drive_text, drive_energy_cost_text, speed_text, turn_rate_text, shuttles_text, fighters_text, bombers_text, sensor_strength_text, ship_energy_cost_text)
    set_variable(_SHIP_TYPE_SPECIFICATIONS_GUI_ELEMENTS_VAR_NAME, elements)

_SHIP_TYPE_SPECIFICATIONS_GUI_ELEMENTS_VAR_NAME = "_ship_type_specifications_gui_elements"
