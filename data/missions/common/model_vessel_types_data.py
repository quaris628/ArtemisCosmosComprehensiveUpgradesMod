
class VesselTypesData:
    def __init__(self, craft_types_by_key, ship_types_by_key, ship_types_by_origin_and_name, ship_type_name_csvs_by_origin):
        self._craft_types_by_key = craft_types_by_key
        self._ship_types_by_key = ship_types_by_key
        self._ship_types_by_origin_and_name = ship_types_by_origin_and_name
        self._ship_type_name_csvs_by_origin = ship_type_name_csvs_by_origin
        self._all_origins_csv = ",".join(ship_type_name_csvs_by_origin.keys())
    
    # Do throw exceptions if key is not found
    # You'd have to either be hardcoding an invalid key in the code
    # or using an invalid key in one of the config files for this to happen.
    # In that situation it's probably better to fail fast and get a clear error
    # sooner than risk downstream problems where the causal link gets less clear.
    
    def get_craft_type_from_key(self, craft_type_key):
        return self._craft_types_by_key[craft_type_key]
    
    def get_ship_type_from_key(self, ship_type_key):
        return self._ship_types_by_key[ship_type_key]
    
    def get_ship_type_from_origin_and_name(self, origin, ship_type_name):
        return self._ship_types_by_origin_and_name[(origin, ship_type_name)]
    
    def get_ship_type_name_csvs_for_origin(self, origin):
        return self._ship_type_name_csvs_by_origin[origin]
    
    def get_all_origins_csv(self):
        return self._all_origins_csv
    
    def get_all_origins(self):
        return self._ship_type_name_csvs_by_origin.keys()
    
    def get_first_ship_type_of_origin(self, origin):
        ship_type_name_csvs = self.get_ship_type_name_csvs_for_origin(origin)
        right_index = ship_type_name_csvs.find(",")
        if right_index < 0:
            first_ship_type_name = ship_type_name_csvs
        else:
            first_ship_type_name = ship_type_name_csvs[:right_index]
        return self.get_ship_type_from_origin_and_name(origin, first_ship_type_name)
    
    def get_last_ship_type_of_origin(self, origin):
        ship_type_name_csvs = self.get_ship_type_name_csvs_for_origin(origin)
        left_index = ship_type_name_csvs.rfind(",") + 1
        if left_index == 0:
            first_ship_type_name = ship_type_name_csvs
        else:
            first_ship_type_name = ship_type_name_csvs[left_index:]
        return self.get_ship_type_from_origin_and_name(origin, first_ship_type_name)
    
    def get_ship_type_key_after(self, ship_type_key):
        ship_type = self.get_ship_type_from_key(ship_type_key)
        ship_type_names = self._ship_type_name_csvs_by_origin[ship_type.origin].split(",")
        current_ship_type_name_index = ship_type_names.index(ship_type.ship_type_name)
        if current_ship_type_name_index + 1 == len(ship_type_names):
            # increment origin too
            origins = self._all_origins_csv.split(",")
            current_origin_index = origins.index(ship_type.origin)
            next_origin_index = 0 if current_origin_index + 1 == len(origins) else current_origin_index + 1
            return self.get_first_ship_type_of_origin(origins[next_origin_index])
        else:
            return self.get_ship_type_from_origin_and_name(ship_type.origin, ship_type_names[current_ship_type_name_index + 1])
    
    def get_ship_type_key_before(self, ship_type_key):
        ship_type = self.get_ship_type_from_key(ship_type_key)
        ship_type_names = self._ship_type_name_csvs_by_origin[ship_type.origin].split(",")
        current_ship_type_name_index = ship_type_names.index(ship_type.ship_type_name)
        if current_ship_type_name_index == 0:
            # decrement origin too
            origins = self._all_origins_csv.split(",")
            current_origin_index = origins.index(ship_type.origin)
            next_origin_index = len(origins) - 1 if current_origin_index == 0 else current_origin_index - 1
            return self.get_last_ship_type_of_origin(origins[next_origin_index])
        else:
            return self.get_ship_type_from_origin_and_name(ship_type.origin, ship_type_names[current_ship_type_name_index - 1])
