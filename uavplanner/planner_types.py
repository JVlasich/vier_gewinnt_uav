from dataclasses import dataclass, field


@dataclass
class MissionParams:
    """Mission Parameters passed to the geometry functions"""
    altitude: float         # m
    velocity: float         # m/s
    fov: float              # ° full angle, converted to rad in metrics
    flight_azimuth: float   # ° clockwise from north
    overlap: float          # fraction 0..1
    lead_in: float          # m
    epsg: int | None = None # None -> pick UTM zone automatically
    prf: float | None = None        # pulses/s, needed for point density
    mission_type: str = "single_grid"
    restricted: bool = False        # route transits inside the AOI (no-fly outside)


@dataclass
class Waypoint:
    """A single Waypoint"""
    lon: float; lat: float; alt_m: float
    velocity: float | None = None
    actions: list[str] = field(default_factory=list)


@dataclass
class FlightLine:
    """A single flight line"""
    index: int; start: Waypoint; end: Waypoint
    transit_to_next: list[Waypoint] = field(default_factory=list)


@dataclass
class Metrics:
    """Metrics for presentation after the calculations
    most importantly: estimated point density"""
    swath: float
    line_spacing: float
    num_lines: int

    point_density: float | None
    total_length: float
    est_duration: float
    warnings: list[str]


@dataclass
class FlightPlan:
    """Finished flight plan that gets exported"""
    lines: list[FlightLine]
    crs_epsg: int
    metrics: Metrics

    def waypoints(self) -> list[Waypoint]:
        out = []
        for line in self.lines:
            out.append(line.start)
            out.append(line.end)
            out.extend(line.transit_to_next)
        return out

