from bisect import bisect_left

class ConsoleSlotsContainer:
    def __init__(self, console_slots_iterable):
        self._console_slots_dict = {}
        for console_slot in console_slots_iterable:
            self._console_slots_dict[console_slot.identifier] = console_slot
        self._client_console_slot_selections_index = {}
        self._at_least_one_console_selected_changed_subscriptions = set()
    
    def get_all_console_slot_identifiers(self):
        return self._console_slots_dict.keys()
    
    def get_all_console_slots(self):
        return self._console_slots_dict.values()
    
    def get_console_slot(self, identifier):
        if identifier not in self._console_slots_dict:
            return None
        return self._console_slots_dict[identifier]
    
    def get_all_console_slots_count(self):
        return len(self._console_slots_dict)
    
    def get_console_slots_selected_by_client(self, client_id):
        if client_id not in self._client_console_slot_selections_index:
            return []
        return self._client_console_slot_selections_index[client_id]
    
    def is_at_least_one_console_selected_by_client(self, client_id):
        return client_id in self._client_console_slot_selections_index
    
    def subscribe_to_at_least_one_console_selected_changed(self, function_to_run):
        self._at_least_one_console_selected_changed_subscriptions.add(function_to_run)
    
    def unsubscribe_from_at_least_one_console_selected_changed(self, function_to_run):
        self._at_least_one_console_selected_changed_subscriptions.remove(function_to_run)
    
    def _on_change_at_least_one_console_selected(self, client_id, is_at_least_one_console_selected):
        for function_to_run in self._at_least_one_console_selected_changed_subscriptions:
            function_to_run(client_id, self, is_at_least_one_console_selected)
    
    def try_select_console(self, client_id, console_identifier):
        if console_identifier not in self._console_slots_dict:
            return False
        console_slot = self._console_slots_dict[console_identifier]
        
        # This should be the same as the result of _try_select
        if not console_slot.is_selectable_by_client(client_id):
            return False
        
        # Update index prior to _try_select b/c it's read from inside _try_select
        if client_id not in self._client_console_slot_selections_index:
            selected_console_slots = []
            self._client_console_slot_selections_index[client_id] = selected_console_slots
            self._on_change_at_least_one_console_selected(client_id, True)
        else:
            selected_console_slots = self._client_console_slot_selections_index[client_id]
        # insert such that sort order is maintained
        insertion_index = bisect_left(selected_console_slots, console_slot)
        # and avoid duplicates
        if insertion_index == len(selected_console_slots) or selected_console_slots[insertion_index] != console_slot:
            selected_console_slots.insert(insertion_index, console_slot)
        
        return console_slot._try_select(client_id)
    
    def deselect_console(self, client_id, console_identifier):
        if console_identifier not in self._console_slots_dict:
            return
        console_slot = self._console_slots_dict[console_identifier]
        
        # Update index prior to _deselect b/c it's read from inside _deselect
        selected_console_slots = self._client_console_slot_selections_index[client_id]
        selected_console_slots.remove(console_slot)
        if len(selected_console_slots) == 0:
            self._client_console_slot_selections_index.pop(client_id)
            self._on_change_at_least_one_console_selected(client_id, False)
        
        console_slot._deselect(client_id)
    
    def deselect_all_consoles(self, client_id):
        if client_id not in self._client_console_slot_selections_index:
            return
        
        # Update index prior to _deselect b/c it's read from inside _deselect
        self._client_console_slot_selections_index.pop(client_id, None)
        
        for console_slot in self._console_slots_dict.values():
            console_slot._deselect(client_id)
        
        self._on_change_at_least_one_console_selected(client_id, False)
