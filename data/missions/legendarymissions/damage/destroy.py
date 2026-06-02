from sbs_utils.procedural.roles import has_role
from sbs_utils.procedural.links import get_dedicated_link

def get_player_capital_ship_attributed_to_damage(damage_source_id, damage_parent_id):
    """
    Gets the player capital ship that caused a damage event.
    
    If no player ship caused the damage, returns None.
    
    These are all the possible causal links to a player ship:
    Beams fired by a player ship
    Ordinance* fired by a player ship
    Beams fired by single-seat craft whose 'home dock' is a player ship
    Ordinance* fired by single-seat craft whose 'home dock' is a player ship
    
    *Who dropped a mine is not consistently detected due to this bug:
    https://github.com/artemis-sbs/LegendaryMissions/issues/495
    
    Args:
        damage_source_id (int | None): DAMAGE_SOURCE_ID from //damage/ event
        damage_parent_id (int | None): DAMAGE_PARENT_ID from //damage/ event
    Returns:
        (int | None) if a player ship caused the damage, id of that player ship;
            otherwise None
    """
    
    if has_role(damage_source_id, "__player__"):
        return damage_source_id
    elif has_role(damage_parent_id, "__player__"):
        return damage_parent_id
    elif has_role(damage_source_id, "cockpit"):
        home_dock_id = get_dedicated_link(damage_source_id, "home_dock")
        if has_role(home_dock_id, "__player__"):
            return home_dock_id
    elif has_role(damage_parent_id, "cockpit"):
        home_dock_id = get_dedicated_link(damage_parent_id, "home_dock")
        if has_role(home_dock_id, "__player__"):
            return home_dock_id
    return None

def get_player_single_seat_craft_attributed_to_damage(damage_source_id, damage_parent_id):
    """
    Gets the player single-seat craft (shuttle, fighter, or bomber) that caused
    a damage event.
    
    If no player single-seat craft caused the damage, returns None.
    
    These are all the possible causal links to a single-seat craft:
    Beams fired by a single-seat craft
    Ordinance* fired by a single-seat craft
    
    *Who dropped a mine is not consistently detected due to this bug:
    https://github.com/artemis-sbs/LegendaryMissions/issues/495
    
    Args:
        damage_source_id (int | None): DAMAGE_SOURCE_ID from //damage/ event
        damage_parent_id (int | None): DAMAGE_PARENT_ID from //damage/ event
    Returns:
        (int | None) if a player single-seat craft caused the damage, id of
            that single-seat craft; otherwise None
    """
    if has_role(damage_source_id, "cockpit"):
        return damage_source_id
    elif has_role(damage_parent_id, "cockpit"):
        return damage_parent_id
    else:
        return None
