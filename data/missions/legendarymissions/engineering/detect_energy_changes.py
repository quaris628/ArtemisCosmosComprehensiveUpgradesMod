from sbs_utils.procedural.execution import task_schedule

# Tasks are scheduled if energy changes to or beyond the listed threshold
def get_increase_triggers():
    return [
        # (energy level, mast label to schedule a task for)
        (4000, "start_overheating"),
    ]

def get_decrease_triggers():
    return [
    ]

def energy_changed_event(event_identifier, player_ship_id):
    task_schedule(event_identifier, data={"PLAYER_SHIP_ID": player_ship_id})
