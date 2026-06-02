from sbs_utils.procedural.signal import signal_emit

from model_console_slots_container import ConsoleSlotsContainer

class PlayerShipSetupData(ConsoleSlotsContainer):
    def __init__(self, number, name, side, ship_type_key, ship_specific_console_slots_iterable, is_destroyed=False):
        super().__init__(ship_specific_console_slots_iterable)
        self._number = number
        self._name = name
        self.side = side
        self._ship_type_key = ship_type_key
        self.spawned_ship_id = None
        self._is_destroyed = is_destroyed
        self._is_destroyed_changed_subscriptions = set()
        self._selected_by_clients = set()
    
    @property
    def number(self):
        return self._number
    
    @property
    def name(self):
        return self._name
    
    @name.setter
    def name(self, val):
        if self._name != val:
            self._name = val
            signal_emit(signal_player_ship_setup_data_name_changed(), {"SHIP": self})
            signal_emit(signal_player_ship_setup_data_name_changed(self.number), {"SHIP": self})
    
    @property
    def ship_type_key(self):
        return self._ship_type_key
    
    @ship_type_key.setter
    def ship_type_key(self, val):
        if self._ship_type_key != val:
            self._ship_type_key = val
            signal_emit(signal_player_ship_setup_data_ship_type_changed(), {"SHIP": self})
            signal_emit(signal_player_ship_setup_data_ship_type_changed(self.number), {"SHIP": self})
    
    @property
    def is_destroyed(self):
        return self._is_destroyed
    
    @is_destroyed.setter
    def is_destroyed(self, val):
        if self._is_destroyed != val:
            self._is_destroyed = val
            signal_emit(signal_player_ship_setup_data_is_destroyed_changed(), {"SHIP": self})
            signal_emit(signal_player_ship_setup_data_is_destroyed_changed(self.number), {"SHIP": self})
            for function_to_run in self._is_destroyed_changed_subscriptions:
                function_to_run(self)
    
    def subscribe_to_is_destroyed_changed(self, function_to_run):
        self._is_destroyed_changed_subscriptions.add(function_to_run)
    
    def unsubscribe_from_is_destroyed_changed(self, function_to_run):
        self._is_destroyed_changed_subscriptions.remove(function_to_run)
    
    def get_selected_by_clients(self, exclude_server=False, exclude_operator_mode=False):
        client_ids = self._selected_by_clients
        if exclude_server:
            client_ids = set(client_ids)
            client_ids.discard(0)
        if exclude_operator_mode:
            # TODO
            pass
        return client_ids
    
    def is_selected_by_client(self, client_id):
        return client_id in self._selected_by_clients
    
    # _select and _deselect should probably only be called from GameSetupData,
    # to help prevent invalid selection data.
    # Consider the _ prefixes a soft warning; only call these if you know what
    # you're doing.
    
    def _select(self, client_id):
        if client_id in self._selected_by_clients:
            return
        self._selected_by_clients.add(client_id)
        signal_emit(signal_player_ship_setup_data_selection_changed(), {"CLIENT_ID": client_id, "SHIP": self, "SELECTED": True})
        signal_emit(signal_player_ship_setup_data_selection_changed(client_id=client_id), {"CLIENT_ID": client_id, "SHIP": self, "SELECTED": True})
    
    def _deselect(self, client_id):
        if client_id not in self._selected_by_clients:
            return
        super().deselect_all_consoles(client_id)
        self._selected_by_clients.remove(client_id)
        signal_emit(signal_player_ship_setup_data_selection_changed(), {"CLIENT_ID": client_id, "SHIP": self, "SELECTED": False})
        signal_emit(signal_player_ship_setup_data_selection_changed(client_id=client_id), {"CLIENT_ID": client_id, "SHIP": self, "SELECTED": False})
    
    # Override
    def try_select_console(self, client_id, console_identifier):
        if client_id not in self._selected_by_clients:
            return False
        return super().try_select_console(client_id, console_identifier)
    
# These have to be standalone functions, not static properties,
# because otherwise MAST can't reference them

# Have the option to subscribe to any ship's data changing OR
# the option to subscibe to only a particular ship's data changing
def signal_player_ship_setup_data_name_changed(ship_number=None):
    return f"pssd_name_changed_{ship_number}"
def signal_player_ship_setup_data_ship_type_changed(ship_number=None):
    return f"pssd_ship_type_changed_{ship_number}"
def signal_player_ship_setup_data_is_destroyed_changed(ship_number=None):
    return f"pssd_is_destroyed_changed_{ship_number}"


def signal_player_ship_setup_data_selection_changed(client_id=None):
    return f"pssd_selection_changed_{client_id}"
