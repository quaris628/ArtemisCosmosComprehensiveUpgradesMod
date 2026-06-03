from random import uniform

from sbs_utils.procedural.inventory import set_inventory_value
from sbs_utils.procedural.spawn import terrain_spawn

def spawn_wreck(position, origin, original_hullpoints, ship_type_key="wreck", name="Wreck"):
    """
    Spawns a wreck.
    Args:
        position (Vec3): position to spawn wreck at
        origin (str): Origin of the ship this wreck came from
        original_hullpoints (int): Hullpoints of the ship this wreck came from
        ship_type_key (str | None): Optional, default "wreck". Key to shipData.yaml.
            Used for the wreck's space object that gets spawned.
            The main reason you might want to set this is to change the wreck's
            appearance on the 3d view. This doesn't affect anything else (to my 
            knowledge).
        name (str | None): Optional, default "Wreck". Name displayed for this wreck
            in the science details box and on the 3d main screen view.
    Returns:
        (SpawnData): The spawn data for the wreck
    """
    # mostly copied from destroy.mast
    
    # We give the wreck a random yaw/pitch (so it spins a bit), set the radar color, and assign some inventory values
    # to help determine later if it drops any particular upgrade.
    
    # note: changed to not use side or exact origin to avoid logic conflicts
    # the role of side/origin wasn't used but confused other logic
    wr = terrain_spawn(position.x, position.y, position.z, name, f"wreck, wreck_{origin}", ship_type_key, "behav_wreck")
    temp_yaw = uniform(0.001, 0.003)
    temp_pitch = uniform(0.002, 0.004)
    wr.engine_object.steer_yaw = temp_yaw
    wr.engine_object.steer_pitch = temp_pitch
    wr.blob.set("radar_color_override", "#f0c")
    
    set_inventory_value(wr.id, "hp", 150)
    wr.py_object.origin = origin
    set_inventory_value(wr.id, "hull_type", original_hullpoints)
    
    return wr
