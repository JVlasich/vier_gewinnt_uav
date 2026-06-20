# geometry.py
from shapely.affinity import rotate
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import substring


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


def route_transits(lines, polygon, restricted) -> list[LineString]:
    """One transit leg per consecutive line pair, in the projected CRS.
    Straight hop unless restricted and the hop leaves the polygon,
    then walk along the boundary instead."""
    safe = polygon.buffer(0.5)
    ring = polygon.exterior
    transits = []
    for prev, nxt in zip(lines, lines[1:]):
        hop = LineString([prev.coords[-1], nxt.coords[0]])
        if restricted and not hop.covered_by(safe):
            hop = _boundary_path(ring, hop.coords[0], hop.coords[-1])
            if not hop.covered_by(safe):
                raise ValueError(
                    "restricted transit still leaves the AOI; the boundary "
                    "walk cannot route around holes")
        transits.append(hop)
    return transits


def _boundary_path(ring, p0, p1) -> LineString:
    """Path from p0 to p1 along the ring, shorter of the two directions."""
    d0 = ring.project(Point(p0))
    d1 = ring.project(Point(p1))
    direct = abs(d1 - d0)
    if direct <= ring.length - direct:
        path = substring(ring, d0, d1)
    else:
        # the shorter way goes through the ring closure point
        if d0 < d1:
            a = substring(ring, d0, 0)
            b = substring(ring, ring.length, d1)
        else:
            a = substring(ring, d0, ring.length)
            b = substring(ring, 0, d1)
        path = LineString(list(a.coords) + list(b.coords)[1:])
    # keep the exact endpoints, projection may have snapped them
    return LineString([p0, *path.coords[1:-1], p1])
