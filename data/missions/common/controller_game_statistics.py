from sbs_utils.fs import load_yaml_string
from sbs_utils.procedural.execution import get_shared_variable, set_shared_variable
from sbs_utils.procedural.grid import grid_get_grid_data
from sbs_utils.procedural.media import media_read_relative_file
from sbs_utils.procedural.ship_data import get_ship_data

from data.missions.common.model_game_statistics import GameStatistics

# ----- Initializing -----

def initialize_game_statistics():
    _set_game_statistics(GameStatistics())

# ----- Setter/getter wrappers -----

def get_game_statistics():
    return get_shared_variable(_GAME_STATISTICS_VAR_NAME)

def _set_game_statistics(setup_data):
    set_shared_variable(_GAME_STATISTICS_VAR_NAME, setup_data)

_GAME_STATISTICS_VAR_NAME = "_game_statistics"
