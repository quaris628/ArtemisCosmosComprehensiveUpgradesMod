from sbs_utils.procedural.query import to_blob, to_object

def has_orientable_beams(ship_id):
    return to_object(ship_id).art_id in { ship_type_pirate_strongbow_ef(), ship_type_pirate_brigantine_ef() }

def orient_beams_forward(ship_id):
    ship_type = to_object(ship_id).art_id
    ship_blob = to_blob(ship_id)
    if ship_blob is None:
        return
    # these should match the angles in shipData.yaml
    elif ship_type == ship_type_pirate_strongbow_ef():
        ship_blob.set(blob_key_beam_angle(), 63.88, 2)
        ship_blob.set(blob_key_beam_angle(), 296.12, 3)
    elif ship_type == ship_type_pirate_brigantine_ef():
        ship_blob.set(blob_key_beam_angle(), 21, 0)
        ship_blob.set(blob_key_beam_angle(), 339, 1)

def orient_beams_broad(ship_id):
    ship_type = to_object(ship_id).art_id
    ship_blob = to_blob(ship_id)
    if ship_blob is None:
        return
    elif ship_type == ship_type_pirate_strongbow_ef():
        ship_blob.set(blob_key_beam_angle(), 116.12, 2)
        ship_blob.set(blob_key_beam_angle(), 243.88, 3)
    elif ship_type == ship_type_pirate_brigantine_ef():
        ship_blob.set(blob_key_beam_angle(), 90, 0)
        ship_blob.set(blob_key_beam_angle(), 270, 1)

def blob_key_beam_angle():
    return "beamBarrelAngle"

def ship_type_pirate_strongbow_ef():
    return "pirate_strongbow_ef"

def ship_type_pirate_brigantine_ef():
    return "pirate_brigantine_ef"
