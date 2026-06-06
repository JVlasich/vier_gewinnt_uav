from geometry import generate_flight_lines
from shapely.geometry import LineString

def grid(polygon, generate_flight_lines, altitude, fov, direction,overlap=0.7,scan_rate=10):
    return generate_flight_lines(polygon, altitude, fov, direction,overlap)

def perimeter(polygon, generate_flight_lines, altitude, fov, direction):
    coords = list(polygon.exterior.coords)
    boundary = LineString(coords)
    return [boundary]

def crossgrid(polygon, generate_flight_lines, altitude, fov, direction, overlap=0.7, scan_rate=10):
    lines_1 = generate_flight_lines(
        polygon,
        altitude,
        fov,
        direction,
        overlap
    )

    lines_2 = generate_flight_lines(
        polygon,
        altitude,
        fov,
        direction + 90,
        overlap
    )

    return lines_1 + lines_2

def get_mission_type(name):
    return {
        "grid": grid,
        "perimeter": perimeter,
        "crossgrid": crossgrid
    }.get(name)