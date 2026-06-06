import argparse 
from shapely.geometry import Polygon 
from geometry import generate_flight_lines 
from waypoints import lines_to_waypoints 
from geo_loader import load_geojson 
from projection import to_utm 
from mission_types import get_mission_type
from kml_export import export_kml

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--altitude", type=float, required=True)
    parser.add_argument("--fov", type=float, required=True)
    parser.add_argument("--direction", type=float, default=0)
    parser.add_argument("--mission_type", type=str, default="grid")
    parser.add_argument("--speed", type=float, default=5)
    #parser.add_argument("--crossgrid_direction", type=float, default=90)
    parser.add_argument("--overlap", type=float, default=0.7)
    parser.add_argument("--scan_rate", type=float, default=10)

    args = parser.parse_args()

    polygon = load_geojson("area.geojson")
    polygon = to_utm(polygon)

    print("Fläche:", polygon.area)

    mission_fn = get_mission_type(args.mission_type)

    if mission_fn is None:
        raise ValueError("Unknown mission type")

    # 👉 NUR HIER entsteht flight logic
    lines = mission_fn(
        polygon,
        generate_flight_lines,
        altitude=args.altitude,
        fov=args.fov,
        direction=args.direction,
        #crossgrid_direction=args.crossgrid_direction,
        overlap=args.overlap,
        scan_rate=args.scan_rate
    )

    waypoints = lines_to_waypoints(
        lines, 
        altitude=args.altitude,
        speed=args.speed)

    print("Waypoints:", waypoints)
    print("Anzahl Fluglinien:", len(lines))
    export_kml(waypoints, "mission.kml")
if __name__ == "__main__":
    main()
