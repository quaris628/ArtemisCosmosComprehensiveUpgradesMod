from random import choice

import sbs

from sbs_utils.helpers import FrameContext
from sbs_utils.mast.label import label
from sbs_utils.mast_sbs.story_nodes.media import MediaLabel
from sbs_utils.procedural.cosmos import sim_create, sim_resume
from sbs_utils.procedural.execution import AWAIT, END, get_shared_variable, get_variable, set_shared_variable, set_variable
from sbs_utils.procedural.gui import gui_blank, gui_button, gui_image, gui_layout_widget, gui_section, gui_text
from sbs_utils.procedural.inventory import set_inventory_value
from sbs_utils.procedural.links import link, unlink
from sbs_utils.procedural.query import to_space_object
from sbs_utils.procedural.roles import remove_role
from sbs_utils.procedural.settings import settings_get_defaults
from sbs_utils.procedural.signal import signal_emit, signal_register
from sbs_utils.procedural.spawn import player_spawn
from sbs_utils.procedural.timers import delay_app, delay_sim

from game_state import game_state_running, get_game_state, signal_game_setup_initialized, signal_sim_created_for_game_start, signal_sim_wiped_after_game_ended

def initialize_background_skybox_hack():
    if _get_skybox_path() is None:
        _set_skybox_path(get_random_skybox_path())
    if not is_skybox_animation_hack_enabled():
        return
    signal_register(signal_game_setup_initialized(), _bkg_sky_hack_on_game_setup_initialized, server=True)
    signal_register(signal_sim_created_for_game_start(), _bkg_sky_hack_on_sim_created_for_game_start, server=True)
    signal_register(signal_sim_wiped_after_game_ended(), _bkg_sky_hack_on_sim_wipe_after_game_ended, server=True)

@label()
def _bkg_sky_hack_on_game_setup_initialized():
    sim_create()
    _spawn_dummy_ship()
    sim_resume()
    yield END()

@label()
def _bkg_sky_hack_on_sim_created_for_game_start():
    # a new sim should already be running
    _spawn_dummy_ship()
    yield END()

@label()
def _bkg_sky_hack_on_sim_wipe_after_game_ended():
    # a new sim should already be created (but not running)
    _spawn_dummy_ship()
    sim_resume()
    yield END()

def _spawn_dummy_ship():
    dummy_ship_spawn_data = player_spawn(200000, 200, 200000, "dummy_ship_for_skybox", "#,dummy_ship_for_skybox_role", "invisible")
    remove_role(dummy_ship_spawn_data.id, "__player__")
    dummy_ship_spawn_data.engine_object.steer_yaw = 0.0005
    
    _set_skybox_dummy_ship_id(dummy_ship_spawn_data.id)
    signal_emit(_signal_spawned_dummy_ship_for_skybox())

def create_skybox_background_on_client(client_id, force_fallback_to_static_png=False, skip_fake_options_button=False):
    if force_fallback_to_static_png or not is_skybox_animation_hack_enabled():
        gui_section(style="area:0,0-100,400,200;")
        background_image = gui_image(f"data/graphics/{_get_skybox_path()}", fit=2)
        
        # For some reason the "Options" button gets covered up by this image
        # on the console selection gui and (at least sometimes) the game results gui.
        # I'm guessing it has to do with the delay_app workarounds being used or not?
        # So make a replacement button background.
        # Most of the time it should hide behind the actual button anyway, but sometimes it
        # seems to be drawn in front.
        if not skip_fake_options_button:
            gui_section(style="area:0,0,200px,36px;background:#0086cc;")
            gui_blank()
            gui_section(style="area:2px,2px,198px,34px;background:#002e40;")
            gui_blank()
        
        return background_image
    
    skybox_dummy_ship_id = _get_skybox_dummy_ship_id()
    old_assigned_ship_id = sbs.get_ship_of_client(client_id)
    
    if skybox_dummy_ship_id is not None:
        if old_assigned_ship_id != skybox_dummy_ship_id:
            
            sbs.assign_client_to_ship(client_id, skybox_dummy_ship_id)
            set_inventory_value(client_id, "CONSOLE_TYPE", "mainscreen")
            unlink(old_assigned_ship_id, "consoles", client_id)
            link(skybox_dummy_ship_id, "consoles", client_id)
            
            if get_variable("has_client_set_sky_box_for_background_hack") is None:
                # Each call of .set_sky_box will freeze the game window
                # for a whole second or so
                # So don't run it unless we absolutely have to
                FrameContext.context.sbs.set_sky_box(client_id, _get_skybox_path())
                set_variable("has_client_set_sky_box_for_background_hack", True)
    else:
        # If the skybox dummy ship isn't spawned yet,
        # then the handler for the spawned signal should reassign the client later,
        # but we still want to clear the client's previous ship assignment now.
        
        # Unfortunately, there doesn't seem to be a good way to clear it.
        # Assigning to ship id 0 is done in the vanilla hangar code, but it
        # 1) doesn't really seem valid to me and 2) assigning to ship id 0
        # happening when entering console selection was a necessary step in
        # reproducing hard crashes whenever clients switch from mainscreen
        # or cinematic consoles to console selection.
        # TODO maybe there's a way to handle this better
        # Maybe don't create the widget before assigning the ship?
        pass
    
    # We want to zoom in on a small rectangle of the 3d view widget
    # Top is just below the heading tick marks - ~12.5% height from the top
    # Bottom is just above the horizon indicator - ~46% height from the top
    # Left is as far left as you can go - 0% width
    # Right is just left of the attitude tick marks - ~88% width from the left
    # After doing some math and adding a little extra margin, I believe the
    # below dimensions should achieve this.
    gui_section(style="area:0,0-40,115,270;")
    gui_layout_widget("3dview")
    
    signal_register(_signal_spawned_dummy_ship_for_skybox(), _reassign_client_to_dummy_ship_for_skybox, is_temporary=True)
    return None

@label()
def _reassign_client_to_dummy_ship_for_skybox():
    client_id = get_variable("client_id")
    skybox_dummy_ship_id = _get_skybox_dummy_ship_id()
    if skybox_dummy_ship_id is None:
        return
    # Don't overwrite the client's actually-assigned ship
    if to_space_object(sbs.get_ship_of_client(client_id)) is not None:
        return
    sbs.assign_client_to_ship(client_id, skybox_dummy_ship_id)
    yield END()

def _signal_spawned_dummy_ship_for_skybox():
    return "spawned_dummy_ship_for_skybox"

def get_random_skybox_path():
    """
    Current possibilities for skybox paths
    (this is configurable per-mission-script;
    see legendarymissions/basic_random_skybox folder)
    
    sky1
    sky1-blue
    sky1-blue
    sky1-ds9
    sky1-rainbow
    sky1-bored-alice
    sky1-delight
    sky1-neb2-rvb
    """
    return choice(MediaLabel.get_of_type("skybox", None)).true_path()
    # chosen by a fair die roll
    # guaranteed to be random
    #return "sky1-neb2-rvb"

# ----- setter/getter wrappers -----

def _get_skybox_dummy_ship_id():
    return get_shared_variable(_SKYBOX_DUMMY_SHIP_ID_VAR_NAME)

def _set_skybox_dummy_ship_id(ship_id):
    set_shared_variable(_SKYBOX_DUMMY_SHIP_ID_VAR_NAME, ship_id)

_SKYBOX_DUMMY_SHIP_ID_VAR_NAME = "SKYBOX_DUMMY_SHIP_ID"

def _get_skybox_path():
    path = get_shared_variable(_SKYBOX_PATH_VAR_NAME)
    if path is None:
        path = get_random_skybox_path()
        _set_skybox_path(path)
    return path

def _set_skybox_path(path):
    set_shared_variable(_SKYBOX_PATH_VAR_NAME, path)

_SKYBOX_PATH_VAR_NAME = "SKYBOX_PATH"

def is_skybox_animation_hack_enabled():
    SETTINGS = settings_get_defaults()
    is_enabled = SETTINGS.get("ENABLE_ANIMATED_SKYBOX_BACKGROUND_HACK", False)
    return is_enabled
