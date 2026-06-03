from sbs_utils.procedural.execution import task_schedule

# For resistor coils and apu triggers, note the duplicate logic in these locations:
# energy_management_controls.py > _auto_should_warp_resistor_coils_be_on
# energy_management_controls.py > _auto_should_apu_be_on

# Tasks are scheduled if energy changes to or beyond the listed threshold
def get_increase_triggers():
    return [
        # (energy level, mast label to schedule a task for)
        (1000, "auto_deactivate_apu"),
        (4000, "auto_activate_warp_resistor_coils"),
        (4000, "start_overheating"),
    ]

def get_decrease_triggers():
    return [
        (999, "auto_activate_apu"),
        (3999, "auto_deactivate_warp_resistor_coils"),
    ]

def energy_changed_event(event_identifier, player_ship_id):
    task_schedule(event_identifier, data={"PLAYER_SHIP_ID": player_ship_id})
