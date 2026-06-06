import argparse
from shapely.geometry import Polygon
from geometry import generate_flight_lines
from waypoints import lines_to_waypoints
from geo_loader import load_geojson

def main():

    parser = argparse.ArgumentParser()

    parser.add_argument("--altitude", type=float, required=True)
    parser.add_argument("--fov", type=float, required=True)
    parser.add_argument("--direction", type=float, default=0)

    args = parser.parse_args()

    # TEST-Polygon (später GeoJSON ersetzen)
    polygon = load_geojson("area.geojson")

    lines = generate_flight_lines(
        polygon,
        args.altitude,
        args.fov,
        args.direction
    )
    waypoints = lines_to_waypoints(lines, altitude=args.altitude)

    print(waypoints)
    print("Anzahl Fluglinien:", len(lines))
    print(lines)

if __name__ == "__main__":
    main()
    
