from dataclasses import dataclass

from data.missions.common.model_vessel_type import VesselType
from data.missions.common.model_single_seat_craft_type import CraftCategory, SingleSeatCraftType

@dataclass(frozen=True, eq=False)
class PlayerCapitalShipType(VesselType):
    tube_count: int
    has_warp_drive: bool
    has_jump_drive: bool
    ship_energy_cost: float
    warp_energy_cost: float
    jump_energy_cost: float
    single_seat_craft_types: dict[CraftCategory, SingleSeatCraftType]
    single_seat_craft_counts: dict[CraftCategory, int]
    
    # Override
    def get_short_description(self):
        if self.has_warp_drive and self.has_jump_drive:
            drive_description = "Hybrid drive"
        elif self.has_warp_drive:
            drive_description = "Warp drive"
        elif self.has_jump_drive:
            drive_description = "Jump drive"
        else:
            drive_description = "Impulse drive"
        
        if self.tube_count == 0 and len(self.beams) == 0:
            weapons_description = "Unarmed"
        elif len(self.beams) == 0:
            weapons_description = f"{self.tube_count} tube{'' if self.tube_count == 1 else 's'}"
        elif self.tube_count == 0:
            weapons_description = super().get_short_description()
        else:
            weapons_description = f"{super().get_short_description()}, {self.tube_count} tube{'' if self.tube_count == 1 else 's'}"
        
        if sum(self.single_seat_craft_counts.values()) == 0:
            single_seat_craft_description = ""
        else:
            single_seat_craft_description = "".join([f", {count} {str(craft_category).title() if craft_category is not None else 'Other single-seat craft'}{'' if count == 1 else 's'}" for craft_category, count in self.single_seat_craft_counts.items() if 0 < count])
        
        return f"{drive_description}, {weapons_description}{single_seat_craft_description}"
