from dataclasses import dataclass

@dataclass(frozen=True, eq=True)
class Beam:
    cycle_time: float
    damage_coeff: float
    range: float
    arcwidth: float
    barrel_angle: float
    
    # Properties affect the sort order in this priority:
    # damage
    # cycle time (inverted)
    # range
    # barrel angle front-to-back
    # barrel angle left-to-right
    # arc width
    def __lt__(self, other):
        if self.damage_coeff != other.damage_coeff:
            return self.damage_coeff < other.damage_coeff
        elif self.cycle_time != other.cycle_time:
            return self.cycle_time > other.cycle_time
        elif self.range != other.range:
            return self.range < other.range
        elif abs(self.barrel_angle - 180) != abs(other.barrel_angle - 180):
            return abs(self.barrel_angle - 180) < abs(other.barrel_angle - 180)
        elif self.barrel_angle != other.barrel_angle:
            return self.barrel_angle > other.barrel_angle
        elif self.arcwidth != other.arcwidth:
            return self.arcwidth < other.arcwidth
        else:
            return False
    
    def __gt__(self, other):
        return self != other and not self < other
    def __le__(self, other):
        return self == other or self < other
    def __ge__(self, other):
        return self == other or self > other

@dataclass(frozen=True, eq=False)
class VesselType:
    # TODO rename these
    ship_type_key: str
    ship_type_name: str
    origin: str
    description: str
    max_ordinance_counts: dict[str, int]
    turn_rate: float
    speed_coeff: float
    scan_strength_coeff: float
    roles: float
    shields: list[float]
    hullpoints: float
    beams: list[Beam]
    
    def get_short_description(self):
        return f"{len(self.beams)} beam{'' if len(self.beams) == 1 else 's'}"
