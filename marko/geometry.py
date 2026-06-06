from shapely.geometry import LineString
from shapely.affinity import rotate
import math
from shapely.geometry import LineString, MultiLineString

def extract_lines(geom):
    if geom.is_empty:
        return []

    if geom.geom_type == "LineString":
        return [geom]

    if geom.geom_type == "MultiLineString":
        return list(geom)

    # Point oder anderes ignorieren
    return []

def generate_flight_lines(polygon, altitude, fov, direction, overlap=0.7, scan_rate=10):
    swath_width = 2 * altitude * math.tan(math.radians(fov / 2))
    spacing = swath_width * (1 - overlap)
    rotated = rotate(polygon, direction, origin='centroid')
    print("POLYGON BOUNDS:", rotated.bounds)
    minx, miny, maxx, maxy = rotated.bounds
    print("SPACING:", spacing)
    lines = []
    y = miny

    while y <= maxy:
        line = LineString([(minx, y), (maxx, y)])
        intersected = rotated.intersection(line)

        lines.extend(extract_lines(intersected))

        y += spacing
    
    
    return lines, scan_rate

