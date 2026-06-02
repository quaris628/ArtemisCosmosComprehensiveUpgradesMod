from dataclasses import dataclass
from enum import StrEnum

from data.missions.common.model_vessel_type import VesselType

class CraftCategory(StrEnum):
    SHUTTLE = "shuttle"
    FIGHTER = "fighter"
    BOMBER = "bomber"

def get_craft_category(roles):
    if CraftCategory.SHUTTLE.value in roles:
        return CraftCategory.SHUTTLE
    elif CraftCategory.FIGHTER.value in roles:
        return CraftCategory.FIGHTER
    elif CraftCategory.BOMBER.value in roles:
        return CraftCategory.BOMBER
    else:
        return None

@dataclass(frozen=True, eq=False)
class SingleSeatCraftType(VesselType):
    category: CraftCategory
    
    # Override
    def get_short_description(self):
        if self.category is None:
            category_description = "Single-seat"
        else:
            category_description = str(self.category).title()
        
        ordinance_description = "".join([f"{ordinance_type.title()}s, " for ordinance_type, count in self.max_ordinance_counts.items() if 0 < count])
        
        return f"{category_description} craft, {ordinance_description}{super().get_short_description()}"
