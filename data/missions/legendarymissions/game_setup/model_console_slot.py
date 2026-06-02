from sbs_utils.procedural.gui.console_types import gui_get_console_type
from sbs_utils.procedural.signal import signal_emit

class ConsoleSlot:
    def __init__(self, identifier, is_exclusive=None, display_name=None, description="", sorting_weight=32768, ship_number=None):
        if display_name is None:
            display_name = identifier
        
        self._identifier = identifier
        self._is_exclusive = is_exclusive
        self._display_name = display_name
        self._description = description
        self._sorting_weight = sorting_weight
        self._ship_number = ship_number
        if is_exclusive:
            self._client_id = None
        else:
            self._client_ids = set()
    
    @property
    def identifier(self):
        return self._identifier
    
    @property
    def is_exclusive(self):
        return self._is_exclusive
    
    @property
    def display_name(self):
        return self._display_name
    
    @property
    def description(self):
        return self._description
    
    @property
    def label(self):
        return gui_get_console_type(self.identifier).label
    
    def is_selected_by_client(self, client_id):
        if self._is_exclusive:
            return client_id == self._client_id
        else:
            return client_id in self._client_ids
    
    def is_exclusively_taken(self):
        return self._is_exclusive and self._client_id is not None
    
    def is_exclusively_taken_by_client(self, client_id):
        return self._is_exclusive and self._client_id == client_id
    
    def is_exclusively_taken_by_another_client(self, client_id):
        return self.is_exclusively_taken() and self._client_id != client_id
    
    # Must match result of _try_select (without actually selecting)
    def is_selectable_by_client(self, client_id):
        return self.is_selected_by_client(client_id) or (not self.is_exclusively_taken())
    
    # _try_select and _deselect should probably only be called from
    # ConsoleSlotContainer, to help prevent invalid selection data.
    # Consider the _ prefixes a soft warning; only call these if you know what
    # you're doing.
    
    def _try_select(self, client_id):
        if self.is_selected_by_client(client_id):
            return True
        elif self.is_exclusively_taken():
            return False
        if self._is_exclusive:
            self._client_id = client_id
            signal_emit(signal_console_slot_is_exclusively_taken_changed(), {"SHIP_NUMBER": self._ship_number, "CONSOLE_SLOT": self})
        else:
            self._client_ids.add(client_id)
        signal_emit(signal_console_slot_deselect_or_select(client_id), {"SHIP_NUMBER": self._ship_number, "CONSOLE_SLOT": self, "IS_SELECT": True})
        return True
    
    def _deselect(self, client_id):
        if not self.is_selected_by_client(client_id):
            return
        if self._is_exclusive:
            self._client_id = None
            signal_emit(signal_console_slot_is_exclusively_taken_changed(), {"SHIP_NUMBER": self._ship_number, "CONSOLE_SLOT": self})
        else:
            self._client_ids.remove(client_id)
        signal_emit(signal_console_slot_deselect_or_select(client_id), {"SHIP_NUMBER": self._ship_number, "CONSOLE_SLOT": self, "IS_SELECT": False})
    
    # sorting operator overloads
    
    def __eq__(self, other):
        return self.identifier == other.identifier
    def __lt__(self, other):
        return self._sorting_weight < other._sorting_weight or (self._sorting_weight == other._sorting_weight and self.identifier < self.identifier)
    
    # based solely on definitions of == and <
    def __ne__(self, other):
        return not(self == other)
    def __gt__(self, other):
        return not(self == other) and not(self < other)
    def __le__(self, other):
        return self == other or self < other
    def __ge__(self, other):
        return self == other or not(self < other)

# This has to be a standalone function, not a static property,
# because otherwise MAST can't reference it
def signal_console_slot_is_exclusively_taken_changed():
    return "cs_is_exclusively_taken_changed"
def signal_console_slot_deselect_or_select(client_id):
    return f"cs_deselect_or_select_{client_id}"
