# missions.py
from typing import Callable
from shapely.geometry import LineString

from .geometry import generate_flight_lines
import math

_missions: dict[str, Callable] = {}    # the registry: name -> function

def register(name: str):
    """Decorator factory: returns a decorator that files fn under name."""
    def decorator(fn):
        _missions[name] = fn           # register the function in the dict
        return fn                      # nothing ever happens
    return decorator

def get_mission_function(name: str) -> Callable:
    try:
        return _missions[name]
    except KeyError:
        raise ValueError(f"unknown mission type {name}; we have {list(_missions)}")


@register("single_grid")
def single_grid(polygon_proj, params, spacing_m) -> list[LineString]:
    return generate_flight_lines(polygon_proj, spacing_m,
                                 params.flight_azimuth, params.lead_in)

@register("double_grid")
def double_grid(polygon_proj, params, spacing_m) -> list[LineString]:
    """Crosshatch: one pass along the azimuth, one perpendicular to it."""
    first = generate_flight_lines(polygon_proj, spacing_m,
                                  params.flight_azimuth, params.lead_in)
    second = generate_flight_lines(polygon_proj, spacing_m,
                                   params.flight_azimuth + 90, params.lead_in)
    return first + second

# TODO: Corridor
@register("corridor")
def corridor(polygon_proj, params, spacing_m) -> list[LineString]:
    """Long, narrow AOI (road, pipeline, river): the drone follows the
    corridor's actual centerline instead of a straight raster azimuth,
    so curves and bends in the corridor are tracked. If the corridor is
    wider than one swath, parallel lines are offset to either side of
    the centerline, spaced spacing_m apart."""
    centerline = _centerline(polygon_proj)
    if centerline is None or centerline.length == 0:
        raise ValueError("corridor: could not derive a centerline from this AOI")

    n_lines = max(1, round((polygon_proj.area / centerline.length) / spacing_m))
    if n_lines == 1:
        offsets = [0.0]
    else:
        start = -(n_lines - 1) / 2 * spacing_m
        offsets = [start + i * spacing_m for i in range(n_lines)]

    # group line pieces by offset (a single offset can split into
    # several disconnected pieces where the corridor narrows below
    # that offset, e.g. near a kink) so the meander order below only
    # ever alternates direction "within a row", never jumps between
    # unrelated pieces of different offsets
    rows: list[list[LineString]] = []
    for off in offsets:
        track = centerline if off == 0.0 else centerline.offset_curve(off)
        if track.is_empty:
            continue
        clipped = track.intersection(polygon_proj)
        parts = getattr(clipped, "geoms", [clipped])
        pieces = [p for p in parts if p.geom_type == "LineString" and p.length > 0]
        if not pieces:
            continue
        # a split offset can produce pieces in arbitrary order; sort
        # them along the centerline so consecutive pieces are adjacent
        pieces.sort(key=lambda p: centerline.project(p.centroid))
        rows.append([_extend(p, params.lead_in) for p in pieces])

    if not rows:
        raise ValueError("corridor: no flight lines fit inside the AOI")

    # meander: alternate direction line-by-line, so the drone always
    # flies from the end of one piece into the start of the next
    ordered = []
    i = 0
    for row in rows:
        for piece in row:
            ordered.append(LineString(piece.coords[::-1]) if i % 2 else piece)
            i += 1

    # split every piece into straight point-to-point segments along the
    # curve: planner.py keeps only the first/last coordinate of each
    # returned LineString, so a single long curved piece would become a
    # straight chord that cuts across the corridor and leaves the AOI
    # between bends. Each short segment stays inside the AOI on its own.
    segments = []
    for piece in ordered:
        coords = list(piece.coords)
        for p0, p1 in zip(coords, coords[1:]):
            segments.append(LineString([p0, p1]))
    return segments


def _centerline(polygon_proj) -> LineString | None:
    """Centerline of a long, narrow polygon. The corridor's two short
    end edges are found first (the ring's two shortest, non-adjacent
    edges -- a corridor's cross-ends are short compared to its long
    sides, unlike the longest point-to-point distance, which is the
    rectangle's diagonal and cuts the ring in the wrong place). Their
    midpoints split the ring into its two long sides; each point on
    the longer side is then paired with its nearest point on the other
    side, and the centerline runs through the midpoints of those
    pairs. Falls back to None if the polygon has too few vertices."""
    coords = list(polygon_proj.exterior.coords[:-1])
    n = len(coords)
    if n < 4:
        return None

    edges = []
    for i in range(n):
        j = (i + 1) % n
        edges.append((math.dist(coords[i], coords[j]), i, j))
    edges.sort(key=lambda e: e[0])
    _, a0, a1 = edges[0]
    second = next((e for e in edges[1:] if a0 not in e[1:] and a1 not in e[1:]), None)
    if second is None:
        return None
    _, b0, b1 = second

    # split the ring into two arcs at the midpoints of these end edges
    arc_a = coords[a1:b0 + 1] if a1 <= b0 else coords[a1:] + coords[:b0 + 1]
    arc_b = coords[b1:a0 + 1] if b1 <= a0 else coords[b1:] + coords[:a0 + 1]
    if len(arc_a) < 1 or len(arc_b) < 1:
        return None
    arc_b = list(reversed(arc_b))

    longer, other = (arc_a, arc_b) if len(arc_a) >= len(arc_b) else (arc_b, arc_a)
    mid_points = []
    for p in longer:
        nearest = min(other, key=lambda q: math.dist(p, q))
        mid_points.append(((p[0] + nearest[0]) / 2, (p[1] + nearest[1]) / 2))
    if len(mid_points) < 2:
        return None
    return LineString(mid_points)


def _extend(line: LineString, lead_in_m: float) -> LineString:
    """Stretch both ends of line outward by lead_in_m, along the
    direction of the line's first/last segment."""
    if lead_in_m == 0:
        return line
    coords = list(line.coords)
    (x0, y0), (x1, y1) = coords[0], coords[1]
    d0 = math.hypot(x1 - x0, y1 - y0) or 1.0
    start = (x0 - (x1 - x0) / d0 * lead_in_m, y0 - (y1 - y0) / d0 * lead_in_m)
    (xn1, yn1), (xn, yn) = coords[-2], coords[-1]
    d1 = math.hypot(xn - xn1, yn - yn1) or 1.0
    end = (xn + (xn - xn1) / d1 * lead_in_m, yn + (yn - yn1) / d1 * lead_in_m)
    return LineString([start, *coords[1:-1], end])