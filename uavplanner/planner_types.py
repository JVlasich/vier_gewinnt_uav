from dataclasses import dataclass, field


@dataclass
class MissionParams:
    """Mission Parameters passed to the geometry functions"""
    altitude: float         # m
    velocity: float         # m/s
    fov: float              # ° or rad?
    scan_rate: float        # hz
    flight_azimuth: float   # ° should this be infered? 
    overlap: float          # m 
    lead_in: float          # m  
    epsg: int


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


@dataclass
class Metrics:
    """Metrics for presentation after the calculations
    most importantly: estimated point density"""
    swath: float
    line_spacing: float
    num_lines: int

    along_track_spacing: float | None
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
    def waypoints(self) -> list[Waypoint]: # type: ignore
        pass

