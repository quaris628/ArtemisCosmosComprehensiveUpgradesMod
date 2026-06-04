from random import randrange
from sbs_utils.procedural.comms import comms_broadcast, comms_receive_internal
from sbs_utils.procedural.execution import set_variable

from data.missions.common.pirate_features_definitions import is_looted, set_looted, looting_comms_messages_color

def loot(looted_ship_object, looted_by_player_ship_object):
    """
    Does everything that needs to happen whenever a player ship loots a
    surrendered ship. Namely, marks the surrendered ship as looted, gives loot
    reward to the player ship, and sends comms and shipwide notifications.
    Loot rewards currently include energy and ordinance, and scale based on the
    surrendered ship's maximum shields strength.
    A surrendered ship can only be looted once; if this function is called
    for a looted_ship_object that was already looted, then nothing will happen.
    Args:
        looted_ship_object (space object): the surrendered ship space object that has
            been looted by the player ship
        looted_by_player_ship_object (space object): the player ship space object that
            has looted the surrendered ship
    """
    
    if is_looted(looted_ship_object.id):
        return
    set_looted(looted_ship_object.id)
    
    shield_max_avg = get_average_max_shields(looted_ship_object.data_set)
    # Maybe also scale loot w/ difficulty? Or a slider in server settings? (idea for later)
    
    min_looted_energy = min(100, 2 * shield_max_avg - 100)
    max_looted_energy = 200 + 4 * shield_max_avg
    looted_energy = randrange(min_looted_energy, max_looted_energy)
    
    looted_homings = randrange(1, 3 + shield_max_avg // 100)
    
    # 0/0
    #          0 EMPs/Mines
    # 120/120
    #          0-1 EMPs/Mines
    # 300/300
    #          0-2 EMPs/Mines
    # 500/500
    #          1-3 EMPs/Mines
    # 1000/1000
    #          1-4 EMPs/Mines
    if shield_max_avg < 120:
        looted_emps = 0
        looted_mines = 0
    elif shield_max_avg < 300:
        looted_emps = randrange(0, 2)
        looted_mines = randrange(0, 2)
    elif shield_max_avg < 500:
        looted_emps = randrange(0, 3)
        looted_mines = randrange(0, 3)
    elif shield_max_avg < 1000:
        looted_emps = randrange(1, 4)
        looted_mines = randrange(1, 4)
    else:
        looted_emps = randrange(1, 5)
        looted_mines = randrange(1, 5)
    
    # 0/0
    #          0 Nukes
    # 220/220
    #          0-1 Nukes
    # 440/440
    #          0-2 Nukes
    # 660/660
    #          1-3 Nukes
    # 1320/1320
    #          1-4 Nukes
    if shield_max_avg < 220:
        looted_nukes = 0
    elif shield_max_avg < 440:
        looted_nukes = randrange(0, 2)
    elif shield_max_avg < 660:
        looted_nukes = randrange(0, 3)
    elif shield_max_avg < 1320:
        looted_nukes = randrange(1, 4)
    else:
        looted_nukes = randrange(1, 5)
    
    player_ship_blob = looted_by_player_ship_object.data_set
    player_ship_blob.set("energy", looted_energy + player_ship_blob.get("energy", 0), 0)
    player_ship_blob.set("Homing_NUM", looted_homings + player_ship_blob.get("Homing_NUM", 0), 0)
    player_ship_blob.set("EMP_NUM", looted_emps + player_ship_blob.get("EMP_NUM", 0), 0)
    player_ship_blob.set("Mine_NUM", looted_mines + player_ship_blob.get("Mine_NUM", 0), 0)
    player_ship_blob.set("Nuke_NUM", looted_nukes + player_ship_blob.get("Nuke_NUM", 0), 0)
    
    # ----- Notification of all the aforementioned loot -----
    
    short_message = f"Plundered {looted_ship_object.name}!"
    
    loot_description = f"We successfully looted the ship, {looted_ship_object.name}! We got:\n{looted_energy} energy\n"
    if looted_homings == 1:
        loot_description += "1 Homing\n"
    elif looted_homings > 1:
        loot_description += f"{looted_homings} Homings\n"
    if looted_nukes == 1:
        loot_description += "1 Nuke\n"
    elif looted_nukes > 1:
        loot_description += f"{looted_nukes} Nukes\n"
    if looted_emps == 1:
        loot_description += "1 EMP\n"
    elif looted_emps > 1:
        loot_description += f"{looted_emps} EMPs\n"
    if looted_mines == 1:
        loot_description += "1 Mine\n"
    elif looted_mines > 1:
        loot_description += f"{looted_mines} Mines\n"
    
    set_variable("COMMS_ORIGIN_ID", looted_by_player_ship_object.id)
    msg_color = looting_comms_messages_color()
    comms_broadcast(looted_by_player_ship_object.id, msg=short_message, color=msg_color)
    comms_receive_internal(loot_description, title=short_message, title_color=msg_color)

def get_average_max_shields(ship_blob):
    """
    Calculates the average of each shield facing's maximum possible points
    on a given ship.
    For example, a ship with 200 front and 200 rear shields, a ship with 300 front
    and 100 rear shields, and a ship with a single 200-point shield all have the same
    average maximum shields, namely 200.
    If the ship has no shields, returns zero.
    Args:
        ship_blob (blob): the blob (aka data_set) of the ship
    Returns:
        float: Average maximum shields of the given ship
    """
    shield_count = ship_blob.get("shield_count", 0)
    if shield_count == 0:
        return 0
    shield_max_sum = 0
    for i in range(shield_count):
        shield_max_sum += ship_blob.get("shield_max_val", i)
    return shield_max_sum / shield_count
