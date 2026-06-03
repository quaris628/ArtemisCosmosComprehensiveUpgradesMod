from sbs_utils.procedural.query import to_blob

def manufacture(player_ship_id, ordinance_type):
    """
    Attempts to create a unit of ordinance from energy.
    Fails if the ship has insufficient energy
    or insufficient room to store the ordinance.
    """
    if ordinance_type == ordinance_type_homing():
        energy_diff = -150
    else:
        # might implement later, or might never allow
        return
    count_diff = 1
    _try_convert(player_ship_id, ordinance_type, count_diff, energy_diff)

def to_energy(player_ship_id, ordinance_type):
    """
    Attempts to create energy by deconstructing a unit of ordinance.
    Fails if the ship has insufficient ordinance
    or insufficient capacity to store the energy.
    """
    if ordinance_type == ordinance_type_homing():
        energy_diff = 100
    else:
        # might implement later, or might never allow
        return
    count_diff = -1
    _try_convert(player_ship_id, ordinance_type, count_diff, energy_diff)

# ----- private setters -----

def _try_convert(player_ship_id, ordinance_type, count_diff, energy_diff):
    player_blob = to_blob(player_ship_id)
    new_energy = _get_energy(player_blob) + energy_diff
    # Decreases below minimum energy
    if energy_diff < 0 and new_energy < 0:
        return
    # Increases above maximum energy
    elif 0 < energy_diff and _MAXIMUM_ENERGY < new_energy:
        return
    
    # Ordinance in the tubes is not available for converting to energy,
    # but is counted in the amount of ordinance the ship can store
    old_total_count = _get_total_ordinance_count(player_blob, ordinance_type)
    old_unloaded_count = _get_unloaded_ordinance_count(player_blob, ordinance_type)
    new_total_count = old_total_count + count_diff
    new_unloaded_count = old_unloaded_count + count_diff
    # Decreases below minimum ordinance count
    if count_diff < 0 and new_unloaded_count < 0:
        return
    # Increases above maximum ordinance count
    elif 0 < count_diff and _get_maximum_ordinance_count(player_blob, ordinance_type) < new_total_count:
        return
    
    _set_energy(player_blob, new_energy)
    _set_ordinance_count(player_blob, ordinance_type, new_total_count)

def _set_energy(player_blob, energy):
    player_blob.set(_BLOB_KEY_ENERGY, energy, 0)

def _set_ordinance_count(player_blob, ordinance_type, count):
    player_blob.set(_blob_key_ordinance_count(ordinance_type), count, 0)

# ----- private getters -----

def _get_energy(player_blob):
    return player_blob.get(_BLOB_KEY_ENERGY, 0)

def _get_total_ordinance_count(player_blob, ordinance_type):
    return player_blob.get(_blob_key_ordinance_count(ordinance_type), 0)

def _get_unloaded_ordinance_count(player_blob, ordinance_type):
    count_total = _get_total_ordinance_count(player_blob, ordinance_type)
    count_inside_tubes = 0
    for i in range(player_blob.get(_BLOB_KEY_TUBE_COUNT, 0)):
        # Note an empty tube's blob entry might be either "" or None
        if player_blob.get(_BLOB_KEY_ORDINANCE_TYPE_IN_TUBE, i) == ordinance_type:
            count_inside_tubes += 1
    return count_total - count_inside_tubes

def _get_maximum_ordinance_count(player_blob, ordinance_type):
    return player_blob.get(_blob_key_maximum_ordinance_count(ordinance_type), 0)

# ----- blob data keys -----

_BLOB_KEY_ENERGY = "energy"

def _blob_key_ordinance_count(ordinance_type):
    return f"{ordinance_type}_NUM"

def _blob_key_maximum_ordinance_count(ordinance_type):
    return f"{ordinance_type}_MAX"

_BLOB_KEY_TUBE_COUNT = "torpedo_tube_count"

_BLOB_KEY_ORDINANCE_TYPE_IN_TUBE = "torpedoTubeCurrentType"

# ----- ordinance types -----

def ordinance_type_homing():
    return "Homing"

# ----- misc -----

_MAXIMUM_ENERGY = 1000
