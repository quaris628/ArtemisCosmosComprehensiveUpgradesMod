from dataclasses import dataclass
from enum import IntEnum

class EnvironmentalFrequency(IntEnum):
    NONE = 0
    FEW = 1
    SOME = 2
    LOTS = 3
    MAX = 4
    
    def as_string(self):
        return {
            EnvironmentalFrequency.NONE: "none",
            EnvironmentalFrequency.FEW: "few",
            EnvironmentalFrequency.SOME: "some",
            EnvironmentalFrequency.LOTS: "lots",
            EnvironmentalFrequency.MAX: "max",
        }[self]

def env_freq_from_string(value):
    return EnvironmentalFrequency({
            "none": EnvironmentalFrequency.NONE,
            "few": EnvironmentalFrequency.FEW,
            "some": EnvironmentalFrequency.SOME,
            "lots": EnvironmentalFrequency.LOTS,
            "max": EnvironmentalFrequency.MAX,
        }[value])

@dataclass(eq=False)
class EnvironmentSetupData:
    terrain_freq: EnvironmentalFrequency
    lethal_terrain_freq: EnvironmentalFrequency
    friendly_ships_freq: EnvironmentalFrequency
    monsters_freq: EnvironmentalFrequency
    upgrades_freq: EnvironmentalFrequency
    time_limit_in_minutes: int
    war_time_delay_in_minutes: int
