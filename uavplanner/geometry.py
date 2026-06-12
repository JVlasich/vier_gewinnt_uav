# geometry.py
from shapely.affinity import rotate
from shapely.geometry import LineString, Polygon


def generate_flight_lines(
    polygon_proj: Polygon, spacing_m: float, azimuth_deg: float, lead_in_m: float = 0.0
) -> list[LineString]:
    origin = (polygon_proj.centroid.x, polygon_proj.centroid.y)
    rotated = _rotate(polygon_proj, azimuth_deg, origin)
    candidates = _slice_bbox(rotated, spacing_m)
    segments = _clip_to_polygon(candidates, rotated, lead_in_m)
    ordered = _order_segments(segments)
    # rotate back into the projected CRS
    return [rotate(seg, 90 - azimuth_deg, origin=origin) for seg in ordered]


def _rotate(geom, azimuth_deg, origin):
    """Rotate so the flight direction (azimuth, clockwise from north)
    lands on the x-axis.
    Shapely rotates counterclockwise, azimuth is
    clockwise from north -> -90"""
    return rotate(geom, azimuth_deg - 90, origin=origin)


def _slice_bbox(polygon, spacing_m) -> list[LineString]:
    """Horizontal lines across the bbox, spaced spacing_m apart,
    first offset by spacing_m/2 so none sits exactly on an edge."""
    minx, miny, maxx, maxy = polygon.bounds
    lines = []
    y = miny + spacing_m / 2
    while y < maxy:
        lines.append(LineString([(minx - 1, y), (maxx + 1, y)]))
        y += spacing_m
    return lines


def _clip_to_polygon(lines, polygon, lead_in_m) -> list[LineString]:
    """Keep the parts inside the polygon, left-to-right,
    extended by lead_in_m on both ends."""
    segments = []
    for line in lines:
        clipped = line.intersection(polygon)
        parts = getattr(clipped, "geoms", [clipped])
        for part in parts:
            if not isinstance(part, LineString) or part.length == 0:
                continue
            (x0, y), (x1, _) = part.coords[0], part.coords[-1]
            if x0 > x1:
                x0, x1 = x1, x0
            segments.append(LineString([(x0 - lead_in_m, y), (x1 + lead_in_m, y)]))
    return segments


def _order_segments(segments) -> list[LineString]:
    """Bottom row first, alternate direction every row so each line
    ends near the next one."""
    rows: dict[float, list[LineString]] = {}
    for seg in segments:
        rows.setdefault(round(seg.coords[0][1], 6), []).append(seg)

    ordered = []
    for i, y in enumerate(sorted(rows)):
        row = sorted(rows[y], key=lambda s: s.coords[0][0])
        if i % 2:
            row = [LineString(seg.coords[::-1]) for seg in reversed(row)]
        ordered.extend(row)
    return ordered
