from sbs_utils.procedural.settings import settings_get_defaults

def is_operator_mode_enabled():
    SETTINGS = settings_get_defaults()
    OPERATOR_MODE = SETTINGS.get("OPERATOR_MODE", {"enable": False})
    return OPERATOR_MODE.get("enable", False)
