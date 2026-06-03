
def get_possible_anomaly_types_table(wreck_origin):
    """
    Gets what types of anomalies might be dropped by a wreck if it was destroyed,
    and the weights of how likely it is for each anomaly type to be dropped.
    Args:
        wreck_origin (str): origin of the ship that the wreck used to be
    Returns:
        list[(float, str)]: list of tuples.
            The second value of the tuple is an anomaly type, e.g. "lateral_array".
            The first value of the tuple is a weight, between 0 and 1.
            The sum of all weights in the returned list equals 1.
            The higher an anomly type's weight, the more likely it is to be dropped.
    """
    
    # For most races, they drop three different types of upgrades: Common (50%), Uncommon (30%), and Rare (20%)
    # The upgrades are based loosely on what sort of technology they prefer. Torgoths have the highest shields, so
    # their upgrades are usually shield-based. Ximni have the best beam weapons, so they carry tauron focusers. 
    # Skaraans carry a wide variety of exotic alien technology, so they have an equal chance for every upgrade.
    # If you're adding any new upgrades, make sure you add them to what the Skaraans might drop. 
    
    if wreck_origin == "kralien":
        return [
            (0.5, "lateral_array"),
            (0.3, "hidens_powercell"),
            (0.2, "carapaction_coil")
        ]
    elif wreck_origin == "arvonian":
        return [
            (0.5, "infusion_pcoils"),
            (0.3, "lateral_array"),
            (0.2, "hidens_powercell")
        ]
    elif wreck_origin == "torgoth":
        return [
            (0.5, "carapaction_coil"),
            (0.3, "haplix_overcharger"),
            (0.2, "cetrocite_crystal")
        ]
    elif wreck_origin == "ximni":
        return [
            (0.5, "tauron_focuser"),
            (0.3, "cetrocite_crystal"),
            (0.2, "infusion_pcoils")
        ]
    else: # wreck_origin == "skaraan" or is None or otherwise unrecognized
        # equal chance of all types of anomalies
        return [
            (1/9, "carapaction_coil"),
            (1/9, "infusion_pcoils"),
            (1/9, "tauron_focuser"),
            (1/9, "secret_codecase"),
            (1/9, "hidens_powercell"),
            (1/9, "vigoranium_nodule"),
            (1/9, "cetrocite_crystal"),
            (1/9, "lateral_array"),
            (1/9, "haplix_overcharger")
        ]
