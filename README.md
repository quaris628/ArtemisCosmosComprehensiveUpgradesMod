# Artemis Cosmos Comprehensive Upgrades Mod
Mod for the Artemis Cosmos Spaceship Bridge Simulator game intended to provide bugfixes, quality-of-life enhancements, better parity with Artemis version 2, and other enhancements that generally align with the spirit of the vanilla game.

###  To download the latest version:
1) Go to https://github.com/quaris628/ArtemisCosmosComprehensiveUpgradesMod/releases/latest
2) Download the "Source Code" zip file.

### To install:
1) Unzip the mod files (right-click the zip file you downloaded, then select "Extract All...")
2) Browse to your Artemis Cosmos folder that contains the game files that you wish to apply this mod to. If you bought Artemis Cosmos through steam, you can open this folder from your library by right-clicking Artemis Cosmos in the list of games (on the left), hover over "Manage", then select "Browse local files".
3) Optional, but strongly recommended: Create a backup copy of your entire Artemis Cosmos folder.
4) Take the mod files you extracted and copy them into your Artemis Cosmos folder, such that the mod files overwrite the vanilla files.
5) A window should appear that says the destination already has files with the same names. (If this doesn't happen, then something went wrong in step 4.) When this happens, choose to replace the files in the destination.

### To report bugs, give feedback, etc:

If you believe the bug/feedback/etc is only pertinent to this mod, then create a public issue on github ( https://github.com/quaris628/ArtemisCosmosComprehensiveUpgradesMod/issues ) or you may privately email me at `quaris314@gmail.com`.

If you believe the bug/feedback/etc is only pertinent to vanilla Artemis Cosmos, then create a github issue here: https://github.com/artemis-sbs/LegendaryMissions/issues/new/choose

If you are unsure whether the bug/feedback/etc is pertinent to this mod or vanilla, then assume it's pertinent to this mod; I should be able to sort out which is which, and if it's vanilla I'll forward it.

# List of features:

General/Misc:
- Buttons and other gui elements are colored light blue
- Many buttons and other gui elements have white text, to contrast with background colors better (unforuntately not all text can have its color changed by this mod)
- Add simple 2d map console
- Rearranged widgets of the five main consoles to be more consistent across consoles and different screen sizes
- Fix Engineering, science, and comms widgets not having their custom positions persist between screen refreshes (vanilla feature request [#653](https://github.com/artemis-sbs/LegendaryMissions/issues/653))
- Rename the "Terran" origin to "TSN", to avoid confusion with mostly-terran-pirates

Console selection screen:
- Allow selecting multiple consoles at once (Artemis 2 parity) (vanilla feature request [#475](https://github.com/artemis-sbs/LegendaryMissions/issues/475))
  - Can switch between consoles using tabs along the top of the screen
- Prevent multiple clients from selecting the same console (Artemis 2 parity) (vanilla feature request [#35](https://github.com/artemis-sbs/LegendaryMissions/issues/35))
  - Which consoles do/don't allow multiple clients is configurable in LegendaryMissions/settings.yaml
- Display number of ready and connected clients on each player ship
- Allow opening the help document from console selection
- Allow clients with mainscreen selected to edit their ship name and ship class (Artemis 2 parity)
- Display detailed ship specifications when editing ship name and class
- Display which player ships, if any, have been destroyed (i.e. lost)
- Make background prettier

Game setup screen (normally shows on the server):
- Allow configuring player ship names and ship classes (Artemis 2 parity) (vanilla feature request [#266](https://github.com/artemis-sbs/LegendaryMissions/issues/266))
- Environment settings that are overridden by the currently-selected map are replaced with that overriding value
- Make background prettier

Pause menu:
- Add button to end the game (Artemis 2 parity)
- Add confirmation step to ending the game and rebooting mission scripts
- Make background prettier

Game results screen:
- Display more detailed statistics about the game (Artemis 2 parity)
- Make background prettier

Engineering:
- Increase size of grid node icons by 1.5x
- Overheat systems when energy is over 4000 (Artemis 2 parity)

Mainscreen:
- When opened, show the correct view, facing, and mode (vanilla issues [#595](https://github.com/artemis-sbs/LegendaryMissions/issues/595) and [#291](https://github.com/artemis-sbs/LegendaryMissions/issues/291))
- Different clients will always show the same skybox (vanilla issue [#627](https://github.com/artemis-sbs/LegendaryMissions/issues/627))
- Fix console selection sometimes suddenly switching to mainscreen (vanilla issue [#610](https://github.com/artemis-sbs/LegendaryMissions/issues/610))
- Allow configuring default view, facing, and mode in LegendaryMissions/settings.yaml

Operator mode:
- Allow configuring server to run in quasi-headless mode, in which it will render (almost) nothing on its screen
- Allow configuring which 
- NOTE: The setting to lock clients to specific consoles is not respected by this mod. This is difficult to fix, but I plan to try fixing this in some future version.

These independent mods are included:
- [Unofficial Patch](https://github.com/quaris628/ArtemisCosmosUnofficialPatch)
- [Cheery Beeps Mod](https://github.com/quaris628/ArtemisCosmosCheeryBeepsMod)

#  Compatibility:

Supported vanilla versions:
- 1.3.0

Mission Compatibility:

Mission | Is it ok to run this mission with this mod installed? | Does the Comprehensive Upgrades Mod work? | Other comments
--- | --- | --- | ---
[LegendaryMissions](https://github.com/artemis-sbs/LegendaryMissions) | Yes | Yes |
[remote_mssion_pick](https://github.com/artemis-sbs/remote_mission_pick) | Yes | Yes | Other missions started via remote_mission_pick will have the same compatibility as if they were started via any other way.
All Others | Yes | Partially |

Mod compatibility:

Mod (& version) | Is it ok to install both mods? | In what order should they be installed? | Would the Comprehensive Upgrades Mod work? | Other comments
--- | --- | --- | --- | ---
[Unofficial Patch](https://github.com/quaris628/ArtemisCosmosUnofficialPatch) any version | Yes, but there's no reason to | Unofficial Patch first, Comprehensive Upgrades Mod second | Yes | The Comprehensive Upgrades Mod already includes the Unofficial Patch
[Cheery Beeps Mod](https://github.com/quaris628/ArtemisCosmosCheeryBeepsMod) any version | Yes, but there's no reason to | Any | Yes | The Comprehensive Upgrades Mod already includes the Cheery Beeps Mod
[TSN Mod](https://github.com/tsnrp/TSN-Cosmos-Mod) Conversion | Yes | Comprehensive Upgrades Mod first, TSN mod second | Partially |
[TNG Mod](https://github.com/ScornMandark/Cosmos-TNG-Mod) v0.2.3 | Yes | Comprehensive Upgrades Mod first, TNG mod second. | Partially | The TNG mod hasn't been updated since vanilla 1.3.0 was released, so it might not even be compatible with vanilla 1.3.0.

Disclaimer: I have not tested every mod and mission script combination. Instead, this compatibility information is based on which files are modified/provided by each mod or mission script. Therefore, this information might not be completely accurate.

# Credits

Contributors:
- Quaris

Mission scripting assistance from:
- Doug Reichard
- Astrolamb
- Bassellope

Playtesting and feedback:
- PirateLord
- Bassellope
- Gypsyjuggler
- Asiansnowman
- Bart
- steveoe
- Dave Trinh
- PoingFerret
- Liberty4All
- VonErebos

Special thanks to:
- Thom Robertson for sharing development versions of Artemis Cosmos
- Bassellope for hosting playtests
