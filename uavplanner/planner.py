from .planner_types import MissionParams, FlightPlan, FlightLine, Waypoint
from .crs import pick_utm_epsg, to_projected, to_wgs84
from .metrics import validate, swath_width, line_spacing, compute_metrics
from .missions import get_mission_function

# planner.py
def plan_mission(polygon_wgs84, params: MissionParams) -> FlightPlan:
    # validate -> project -> spacing -> strategy -> unproject
    # -> build FlightPlan -> compute_metrics -> return
    validate(params)

    epsg = params.epsg or pick_utm_epsg(polygon_wgs84)
    polygon_proj = to_projected(polygon_wgs84, epsg)

    spacing = line_spacing(swath_width(params.altitude, params.fov), params.overlap)
    strategy = get_mission_function(params.mission_type)
    lines_proj = strategy(polygon_proj, params, spacing)
    if not lines_proj:
        raise ValueError("no flight lines generated; AOI smaller than line spacing?")

    metrics = compute_metrics(params, lines_proj)

    flight_lines = []
    for i, line_proj in enumerate(lines_proj):
        line = to_wgs84(line_proj, epsg)
        (lon0, lat0), (lon1, lat1) = line.coords[0], line.coords[-1]
        flight_lines.append(FlightLine(
            index=i,
            start=Waypoint(lon0, lat0, params.altitude, velocity=params.velocity),
            end=Waypoint(lon1, lat1, params.altitude),
        ))

    return FlightPlan(lines=flight_lines, crs_epsg=epsg, metrics=metrics)
