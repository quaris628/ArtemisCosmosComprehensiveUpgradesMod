from controller_game_setup_data import get_game_setup_data

from gui_console_selection_ship_checkbox import ship_checkbox_height
from gui_console_selection_console_checkbox import console_checkbox_height

def calculate_main_body_y_offsets_from_50():
    GAME_SETUP_DATA = get_game_setup_data()
    
    # player ship checkbox count + height
    max_player_ship_count = GAME_SETUP_DATA.get_max_player_ship_count()
    # ship_checkbox_height()
    
    # console checkbox counts + height
    max_ship_specific_console_count = get_max_ship_specific_console_count(GAME_SETUP_DATA)
    ship_agnostic_console_count = get_max_ship_agnostic_console_count(GAME_SETUP_DATA)
    # console_checkbox_height()
    
    # heights of each section
    ship_section_height = max_player_ship_count * (ship_checkbox_height() + vertical_space_between_checkboxes())
    ship_specific_consoles_section_height = max_ship_specific_console_count * (console_checkbox_height() + vertical_space_between_checkboxes())
    ship_agnostic_consoles_section_height = ship_agnostic_console_count * (console_checkbox_height() + vertical_space_between_checkboxes())
    
    ship_specific_section_height = max(ship_section_height, ship_specific_consoles_section_height)
    total_height = ship_specific_section_height + ship_agnostic_consoles_section_height
    
    # tops of each section
    ship_specific_section_top_y_offset_from_50 = -int(total_height / 2)
    ship_agnostic_section_top_y_offset_from_50 = ship_specific_section_top_y_offset_from_50 + ship_specific_section_height
    
    # Mast doesn't support reading multiple return values,
    # so use a list instead
    return [ship_specific_section_top_y_offset_from_50, ship_agnostic_section_top_y_offset_from_50]

def vertical_space_between_checkboxes():
    return 8

def get_max_ship_specific_console_count(GAME_SETUP_DATA):
    # Assume that all ships have the same consoles available
    if len(GAME_SETUP_DATA.player_ships) == 0:
        return 0
    else:
        return GAME_SETUP_DATA.get_player_ship_by_number(1).get_all_console_slots_count()

def get_max_ship_agnostic_console_count(GAME_SETUP_DATA):
    return GAME_SETUP_DATA.get_all_console_slots_count()

def offset_from_50_to_position_string(offset_from_50):
    if offset_from_50 < 0:
        return f"50-{-offset_from_50}px"
    else:
        return f"50+{offset_from_50}px"
