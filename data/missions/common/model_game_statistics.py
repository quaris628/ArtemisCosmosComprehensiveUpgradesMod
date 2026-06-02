from datetime import timedelta
from math import floor

from sbs_utils.helpers import FrameContext
from sbs_utils.procedural.roles import role, all_roles, has_role, has_roles

from data.missions.common.controller_vessel_types_data import get_vessel_types_data

class GameStatistics:
    
    def __init__(self):
        self.record_game_start()
    
    def record_game_start(self):
        self._destroyed_counts_by_origin = {}
        for origin in get_vessel_types_data().get_all_origins():
            self._destroyed_counts_by_origin[origin.lower()] = 0
        self._player_ships_destroyed_count = 0
        self._friendly_stations_destroyed_count = 0
        self._friendly_single_seat_destroyed_count = 0
        self._surrendered_count = 0
        self._surrendered_killed_count = 0
        self._player_beams_fired_count = 0
        self._player_ordinance_fired_count = 0
        self._player_successful_docks_count = 0
        self._picked_up_anomaly_count = 0
        self._start_tick_count = FrameContext.sim.time_tick_counter
        self._duration_in_seconds = None
        self._reason_for_end = None
        self._is_successful_end = None
        self._remaining_enemies = None
    
    # ----- vessel destroyed -----
    
    def record_vessel_destroyed(self, vessel_object):
        if has_roles(vessel_object.id, "cockpit,__player__"):
            self._friendly_single_seat_destroyed_count += 1
        elif has_role(vessel_object.id, "__player__"):
            self._player_ships_destroyed_count += 1
        
        # TODO probably shouldn't hardcode "tsn" to be equivalent to friendly
        if has_roles(vessel_object.id, "station,tsn"):
            self._friendly_stations_destroyed_count += 1
        
        # Anomalies (and probably other things too?) have their origin set to "no origin"
        # And these probably shouldn't be counted in the vessels destroyed counts
        if vessel_object.origin is None or vessel_object.origin == "no origin":
            return
        
        lowercase_origin = vessel_object.origin.lower()
        if lowercase_origin in self._destroyed_counts_by_origin:
            self._destroyed_counts_by_origin[lowercase_origin] += 1
        else:
            self._destroyed_counts_by_origin[lowercase_origin] = 1
    
    def get_origin_destroyed_count(self, origin):
        if origin not in self._destroyed_counts_by_origin:
            return 0
        return self._destroyed_counts_by_origin[origin]
    
    def get_origin_destroyed_counts_iterable(self):
        return self._destroyed_counts_by_origin.items()
    
    def get_destroyed_count(self):
        return sum(self._destroyed_counts_by_origin.values())
    
    def get_player_ships_destroyed_count(self):
        return self._player_ships_destroyed_count
    
    def get_friendly_stations_destroyed_count(self):
        return self._friendly_stations_destroyed_count
    
    def get_friendly_single_seat_destroyed_count(self):
        return self._friendly_single_seat_destroyed_count
    
    # ----- vessel surrendered -----
    
    def record_vessel_surrendered(self, vessel_object):
        self._surrendered_count += 1
    
    def get_surrendered_count(self):
        return self._surrendered_count
    
    # ----- player killed surrendered -----
    
    def record_player_killed_surrendered(self, player_ship_id, surrendered_ship_object):
        self._surrendered_killed_count += 1
    
    def get_surrendered_killed_count(self):
        return self._surrendered_killed_count
    
    # ----- player fired beam -----
    
    def record_player_fired_beam(self, player_ship_id):
        self._player_beams_fired_count += 1
    
    def get_player_beams_fired_count(self):
        return self._player_beams_fired_count
    
    # ----- player fired ordinance -----
    
    # TODO record this; waiting on sbs_utils feature to be implemented
    # https://github.com/artemis-sbs/LegendaryMissions/issues/385
    
    def record_player_fired_ordinance(self, player_ship_id):
        self._player_ordinance_fired_count += 1
    
    def get_player_ordinance_fired_count(self):
        #return self._player_ordinance_fired_count
        return "?"
    
    # ----- player successfully docked -----
    
    def record_player_successful_dock(self, player_ship_id):
        self._player_successful_docks_count += 1
    
    def get_player_successful_docks_count(self):
        return self._player_successful_docks_count
    
    # ----- picked up anomaly -----
    
    def record_player_picked_up_anomaly(self, player_ship_id):
        self._picked_up_anomaly_count += 1
    
    def get_player_picked_up_anomaly_count(self):
        return self._picked_up_anomaly_count
    
    # ----- end-of-game -----
    
    def record_game_end(self, reason="mission ended.", is_success=None):
        # Assumes the simulation runs at 30 ticks per second
        # See the commend in preferences.json for the scriptTickDelay setting
        # This is the same math as in vanilla (as of 1.2.7), which I tested with a
        # different scriptTickDelay and it still seemed accurate as far as I could tell.
        self._duration_in_seconds = (FrameContext.sim.time_tick_counter - self._start_tick_count) / 30
        self._reason_for_end = reason
        self._is_successful_end = is_success
        self._remaining_enemies = len(role("raider") | all_roles("enemy,station"))
        # TODO maybe record remaining ordinance and energy of player ships
        # Might be hard to do this if they get destroyed, but that might still be good to do
    
    def get_duration_in_seconds(self):
        return self._duration_in_seconds
    
    def get_duration_in_minutes(self):
        return floor(self._duration_in_seconds / 60)
    
    def get_reason_for_end(self):
        return self._reason_for_end
    
    def is_end_success(self):
        return self._is_successful_end
    
    def get_remaining_enemies(self):
        return self._remaining_enemies
    
