from sbs_utils.procedural.ship_data import get_ship_data_for
from sbs_utils.procedural.query import to_space_object

def get_space_object_type_long_description(space_object_id):
    space_object = to_space_object(space_object_id)
    if space_object is None:
        return ""
    
    space_object_type_data = get_ship_data_for(space_object.art_id)
    if space_object_type_data is None:
        return ""
    
    long_description = space_object_type_data.get("long_desc", "")
    
    return long_description
