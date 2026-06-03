
station_type_key_to_abbrev_map = {
    "starbase_industry": "IND",
    "starbase_command": "CMD",
    "starbase_civil": "CIV",
    "starbase_science": "SCI"
}

def get_station_type_abbrev(station_type_key):
    return station_type_key_to_abbrev_map[station_type_key]
