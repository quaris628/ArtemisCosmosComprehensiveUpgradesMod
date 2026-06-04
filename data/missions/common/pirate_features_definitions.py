"""
For definitions fundamental to features that are (traditionally) for pirates.
Expect these to be referenced by many different places in the code.
"""
from sbs_utils.procedural.execution import get_shared_variable
from sbs_utils.procedural.inventory import get_inventory_value, set_inventory_value
from sbs_utils.procedural.query import to_space_object
from sbs_utils.procedural.roles import has_role

# ----- looting -----

def can_loot(player_ship_id):
    return is_pirate(player_ship_id)

def loot_rendezvous_radius():
    return 500

def is_looted(ship_id):
    """ Returns True if the ship has already had its loot taken, otherwise False """
    return get_inventory_value(ship_id, _inventory_key_is_looted())

def set_looted(ship_id):
    """ Call this to indicate that the ship is having its loot taken """
    set_inventory_value(ship_id, _inventory_key_is_looted(), True)

def _inventory_key_is_looted():
    return "is_looted"

def looting_comms_messages_color():
    return get_shared_variable("surrender_color", "#ff0")

# ----- "side" definitions -----
# TODO update implementations when ship sides get more fleshed out in vanilla?

def is_raider(ship_id):
    """ Excludes enemies that have surrendered """
    return has_role(ship_id, "raider")

def is_pirate(ship_id):
    origin = get_origin(ship_id)
    return origin == "pirate"

def is_tsn(ship_id):
    origin = get_origin(ship_id)
    return origin == "tsn"

def is_ximni(ship_id):
    origin = get_origin(ship_id)
    return origin == "ximni"

# There may be other cases too besides the above
# e.g. apparently players can play as arvonian ships now?
# And custom missions might put player ships on custom sides too

# ----- helpers -----

def get_origin(ship_id):
    ship_object = to_space_object(ship_id)
    if ship_object is None:
        return None
    else:
        return ship_object.origin

def get_ship_type_key(ship_id):
    """ Get this ship's ship type key (the one used in shipData.yaml) """
    ship_object = to_space_object(ship_id)
    if ship_object is None:
        return None
    else:
        return ship_object.art_id
