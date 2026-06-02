
def signal_before_player_ship_destroyed():
    return "before_player_ship_destroyed"

def signal_after_player_ship_destroyed():
    return "after_player_ship_destroyed"

def signal_comms_property_list_box_update_ship_to_ship(player_ship_id):
    return f"comms_property_list_box_update_ship_to_ship_{player_ship_id}"
