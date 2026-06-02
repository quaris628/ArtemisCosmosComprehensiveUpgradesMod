from sbs_utils.procedural.maps import maps_get_list
from sbs_utils.procedural.signal import signal_emit

from model_console_slots_container import ConsoleSlotsContainer

class GameSetupData(ConsoleSlotsContainer):
    def __init__(self, ship_agnostic_console_slots_iterable, player_ships, player_ship_count, difficulty, seed_value, map_identifier, environment_settings):
        super().__init__(ship_agnostic_console_slots_iterable)
        self._player_ships = player_ships
        self._player_ship_count = player_ship_count
        self._clients = {}
        self._index_client_id_to_player_ship = {}
        self.difficulty = difficulty
        self.seed_value = seed_value
        self.map_identifier = map_identifier
        self.environment_settings = environment_settings
        
        for player_ship in self._player_ships.values():
            player_ship.subscribe_to_at_least_one_console_selected_changed(self._on_at_least_one_ship_specific_console_changed)
            player_ship.subscribe_to_is_destroyed_changed(self._on_ship_is_destroyed_changed)
        self.subscribe_to_at_least_one_console_selected_changed(self._on_at_least_one_ship_agnostic_console_changed)
    
    # ----- Player ships + clients -----
    
    @property
    def player_ships(self):
        return self._player_ships
    
    def get_player_ship_by_number(self, number):
        if number not in self._player_ships:
            return None
        return self._player_ships[number]
    
    def get_player_ship_by_spawned_ship_id(self, spawned_player_ship_id):
        # Might be faster if an index was used, but I'd rather keep one source
        # of truth because 1) it's simpler and 2) it completely avoids the risk
        # of de-syncing errors between the index and the source of truth.
        for player_ship_setup_data in self.player_ships.values():
            if player_ship_setup_data.spawned_ship_id == spawned_player_ship_id:
                return player_ship_setup_data
        return None
    
    @property
    def player_ship_count(self):
        return self._player_ship_count
    
    @player_ship_count.setter
    def player_ship_count(self, val):
        val = max(1, min(val, self.get_max_player_ship_count()))
        if self._player_ship_count != val:
            old_player_ship_count = self._player_ship_count
            self._player_ship_count = val
            if self._player_ship_count < old_player_ship_count:
                # note that ship numbers are 1-based
                for ship_number in range(self._player_ship_count + 1, old_player_ship_count + 1):
                    ship = self.get_player_ship_by_number(ship_number)
                    # Shift clients that had selected these now-out-of-bounds ships
                    # to an in-bounds ship instead
                    # (Or they could have no ship selected instead?)
                    # deep copy to avoid modifying the collection while iterating over it
                    for client_id in list(ship.get_selected_by_clients()):
                        self.switch_ship(client_id, self._player_ship_count)
                    
                    signal_emit(signal_game_setup_data_player_ship_availability_changed(), data={"SHIP": ship, "IS_AVAILABLE": False})
                    signal_emit(signal_game_setup_data_player_ship_availability_changed(ship_number), data={"SHIP": ship, "IS_AVAILABLE": False})
            else: # old_player_ship_count < self._player_ship_count
                for ship_number in range(old_player_ship_count + 1, self._player_ship_count + 1):
                    ship = self.get_player_ship_by_number(ship_number)
                    signal_emit(signal_game_setup_data_player_ship_availability_changed(), data={"SHIP": ship, "IS_AVAILABLE": True})
                    signal_emit(signal_game_setup_data_player_ship_availability_changed(ship_number), data={"SHIP": ship, "IS_AVAILABLE": True})
            signal_emit(signal_game_setup_data_player_ship_count_changed(), data={"OLD_PLAYER_SHIP_COUNT": old_player_ship_count})
    
    def get_max_player_ship_count(self):
        return len(self.player_ships)
    
    def add_client(self, client_id, is_ready=False, ship_number=1):
        if ship_number not in self._player_ships:
            return
        self._clients[client_id] = is_ready
        player_ship = self._player_ships[ship_number]
        # Sync the index prior to calling ._select,
        # b/c code listening to signals it emits reads from this index
        self._index_client_id_to_player_ship[client_id] = player_ship
        player_ship._select(client_id)
    
    def remove_client(self, client_id):
        if client_id not in self._clients:
            return
        old_player_ship = self.get_selected_ship(client_id)
        if old_player_ship is not None:
            # Sync the index prior to calling ._select,
            # b/c code listening to signals it emits reads from this index
            self._index_client_id_to_player_ship.pop(client_id)
            old_player_ship._deselect(client_id)
        super().deselect_all_consoles(client_id)
        self._clients.pop(client_id)
    
    def is_client_ready(self, client_id):
        if client_id not in self._clients:
            return None
        return self._clients[client_id]
    
    def client_unready(self, client_id):
        if client_id not in self._clients:
            return
        if self._clients[client_id]:
            self._clients[client_id] = False
            signal_emit(signal_game_setup_data_client_ready_changed(), data={"CLIENT_ID": client_id, "IS_READY": False})
            signal_emit(signal_game_setup_data_client_ready_changed(client_id=client_id), data={"CLIENT_ID": client_id, "IS_READY": False})
    
    def try_client_ready(self, client_id):
        if not self.can_client_ready(client_id):
            return False
        if not self._clients[client_id]:
            self._clients[client_id] = True
            signal_emit(signal_game_setup_data_client_ready_changed(), data={"CLIENT_ID": client_id, "IS_READY": True})
            signal_emit(signal_game_setup_data_client_ready_changed(client_id=client_id), data={"CLIENT_ID": client_id, "IS_READY": True})
        return True
    
    def can_client_ready(self, client_id):
        # If changing this implementation, also update
        # _on_at_least_one_ship_agnostic_console_changed()
        # _on_at_least_one_ship_specific_console_changed()
        if client_id not in self._clients:
            return False
        # Tightly coupled with a signal listener for console selects/deselects in
        # gui_console_selection_ready_control.py > create_ready_control()
        # So if you edit this function's implementation, then you should probably
        # edit/supplement/replace/etc the signal listener in create_ready_control too
        return self.is_at_least_one_console_selected_by_client(client_id, include_ship_specific=True)
    
    def can_client_enter_game(self, client_id):
        # If changing this implementation, also update
        # _on_at_least_one_ship_specific_console_changed()
        # _on_ship_is_destroyed_changed()
        if client_id not in self._clients:
            return False
        # TODO also factor in whether the game is running (i.e. move that check to here)
        selected_ship = self.get_selected_ship(client_id)
        return not (selected_ship.is_destroyed and selected_ship.is_at_least_one_console_selected_by_client(client_id))
    
    def _on_at_least_one_ship_agnostic_console_changed(self, client_id, ignored_var, is_at_least_one_selected):
        selected_ship = self.get_selected_ship(client_id)
        if selected_ship is None or not selected_ship.is_at_least_one_console_selected_by_client(client_id):
            signal_emit(signal_game_setup_data_can_client_ready_changed(client_id), data={"CAN_READY": is_at_least_one_selected})
    
    def _on_at_least_one_ship_specific_console_changed(self, client_id, ship, is_at_least_one_selected):
        if ship.is_destroyed:
            signal_emit(signal_game_setup_data_can_client_enter_game_changed(client_id), data={"CAN_ENTER_GAME": not is_at_least_one_selected})
        if not self.is_at_least_one_console_selected_by_client(client_id, include_ship_specific=False):
            signal_emit(signal_game_setup_data_can_client_ready_changed(client_id), data={"CAN_READY": is_at_least_one_selected})
    
    def _on_ship_is_destroyed_changed(self, ship):
        print(f"_on_ship_is_destroyed_changed ship number={ship.number}")
        for client_id in ship.get_selected_by_clients():
            signal_emit(signal_game_setup_data_can_client_enter_game_changed(client_id), data={"CAN_ENTER_GAME": not ship.is_destroyed})
    
    # Override + Overload
    def is_at_least_one_console_selected_by_client(self, client_id, include_ship_specific=False):
        ship_agnostic_result = super().is_at_least_one_console_selected_by_client(client_id)
        if not include_ship_specific or ship_agnostic_result:
            return ship_agnostic_result
        selected_ship = self.get_selected_ship(client_id)
        if selected_ship is None:
            return False
        return selected_ship.is_at_least_one_console_selected_by_client(client_id)
    
    def get_selected_ship(self, client_id):
        if client_id not in self._index_client_id_to_player_ship:
            return None
        return self._index_client_id_to_player_ship[client_id]
    
    def switch_ship(self, client_id, new_ship_number):
        if new_ship_number not in self._player_ships:
            return None
        old_player_ship = self.get_selected_ship(client_id)
        if old_player_ship is not None:
            if old_player_ship.number == new_ship_number:
                return None
            old_player_ship._deselect(client_id)
        new_player_ship = self._player_ships[new_ship_number]
        new_player_ship._select(client_id)
        self._index_client_id_to_player_ship[client_id] = new_player_ship
        return old_player_ship
    
    def get_all_console_slots_selected_by_client(self, client_id):
        selected_ship = self.get_selected_ship(client_id)
        if selected_ship is None:
            return self.get_console_slots_selected_by_client(client_id)
        else:
            return selected_ship.get_console_slots_selected_by_client(client_id) + self.get_console_slots_selected_by_client(client_id)
    
    # Override
    def try_select_console(self, client_id, console_identifier, fall_back_to_ship_specific=False):
        if super().try_select_console(client_id, console_identifier):
            return True
        selected_ship = self.get_selected_ship(client_id)
        return selected_ship.try_select_console(client_id, console_identifier)
    
    def get_map_object(self):
        for map_object in maps_get_list():
            if map_object.path == self.map_identifier:
                return map_object
        return None
    
    def get_map_display_name(self):
        map_object = self.get_map_object()
        if map_object is None:
            return ""
        return map_object.display_name

def signal_game_setup_data_player_ship_count_changed():
    return "gsd_player_ship_count_changed"

def signal_game_setup_data_player_ship_availability_changed(ship_number=None):
    return f"gsd_player_ship_availability_changed_{ship_number}"

def signal_game_setup_data_client_ready_changed(client_id=None):
    return f"gsd_client_ready_changed_{client_id}"
def signal_game_setup_data_can_client_ready_changed(client_id):
    return f"gsd_can_client_ready_changed_{client_id}"
def signal_game_setup_data_can_client_enter_game_changed(client_id):
    return f"gsd_can_client_enter_game_changed_{client_id}"
