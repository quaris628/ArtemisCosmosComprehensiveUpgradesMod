from sbs_utils.procedural.execution import get_variable, set_variable
from sbs_utils.procedural.settings import settings_get_defaults

def is_operator_mode_enabled():
    return _get_operator_mode_settings().get("enable", False)

def is_operator_mode_logo_on_server_enabled():
    return is_operator_mode_enabled() and _get_operator_mode_settings().get("show_logo_on_main", True)

def get_operator_mode_logo_filepath():
    return _get_operator_mode_settings().get("logo", "media/LegendaryMissions/operator")

def get_operator_mode_pin():
    return _get_operator_mode_settings().get("pin", "000000")

def get_operator_mode_console_after_game_starts():
    return _get_operator_mode_settings().get("console_after_game_starts", "gamemaster")

def is_quasi_headless_server_mode_enabled():
    return is_operator_mode_enabled() and _get_operator_mode_settings().get("quasi_headless_server_mode", False)

def _get_operator_mode_settings():
    return settings_get_defaults().get("OPERATOR_MODE", {})

# these settings are technically not coupled with operator mode, but we'll let it slide

def is_editing_player_ships_disabled():
    return settings_get_defaults().get("SHIP_PICK_READ_ONLY", False)

# TODO figure out a way to respect this while still allowing admin to
# specify each machine's console
# Vanilla uses the client_string_set.txt but that's unreliable
# Can scripts access each client's name? If so maybe use that somehow
# to allow this to persist between restarts?
# Or make restarts not purge all script data and allow configuring
# consoles prior to a point in time that you lock them out or something?
def is_changing_consoles_disabled():
    return not settings_get_defaults().get("CAN_CHANGE_CONSOLE", True)

# ----- setter/getter wrappers -----

def is_client_verified_operator_admin():
    return get_variable(_CLIENT_VERIFIED_OPERATOR_ADMIN_VAR_NAME)

def set_client_verified_operator_admin():
    set_variable(_CLIENT_VERIFIED_OPERATOR_ADMIN_VAR_NAME, True)

_CLIENT_VERIFIED_OPERATOR_ADMIN_VAR_NAME = "_client_verified_operator_admin"
