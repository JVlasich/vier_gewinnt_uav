# writer.py
import simplekml

from .planner_types import FlightPlan


def write_kml(plan: FlightPlan, path: str) -> None:
    """Numbered waypoint placemarks plus the full path as a LineString."""
    kml = simplekml.Kml(name="UAV LiDAR mission")

    waypoints = plan.waypoints()
    for i, wp in enumerate(waypoints, start=1):
        pnt = kml.newpoint(name=str(i))
        pnt.coords = [(wp.lon, wp.lat, wp.alt_m)]
        pnt.altitudemode = simplekml.AltitudeMode.relativetoground
        if wp.velocity is not None:
            pnt.description = f"speed: {wp.velocity} m/s"

    path_line = kml.newlinestring(name="flight path")
    path_line.coords = [(wp.lon, wp.lat, wp.alt_m) for wp in waypoints]
    path_line.altitudemode = simplekml.AltitudeMode.relativetoground
    path_line.style.linestyle.color = simplekml.Color.red
    path_line.style.linestyle.width = 3

    kml.save(path)
