# geometry.py
from shapely.affinity import rotate
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import substring
from .routing import route_transits


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


def best_azimuth(polygon_proj: Polygon, spacing_m: float, lead_in_m: float = 0.0) -> float:
    """Azimuth (deg) that gives the shortest path: flight lines plus
    straight transits"""
    def cost(az):
        lines = generate_flight_lines(polygon_proj, spacing_m, az, lead_in_m)
        if not lines:
            return float("inf")
        transits = route_transits(lines, polygon_proj, restricted=False)
        return sum(line.length for line in lines) + sum(t.length for t in transits)

    # sweep with 10 deg steps
    coarse = min(range(0, 180, 10), key=cost)
    # +-10 fine sweep around coarse result
    fine = float(min(range(coarse - 10, coarse + 11, 2), key=cost))
    return fine


def _rotate(geom, azimuth_deg, origin):
    """Rotate so the flight direction lands on the x-axis."""
    # Shapely rotates counterclockwise, azimuth is clockwise from north -> -90
    return rotate(geom, azimuth_deg - 90, origin=origin)


def _slice_bbox(polygon, spacing_m) -> list[LineString]:
    """Horizontal lines across the bbox, spaced spacing_m apart."""
    minx, miny, maxx, maxy = polygon.bounds
    lines = []
    # first offset by spacing_m/2 -> none sits exactly on the edge.
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
    """Sweep each connected cell of the AOI completely before moving to
    the next. Direction alternates every row within a cell."""
    rows = _group_rows(segments)
    cells = _build_cells(rows)
    cells.sort(key=lambda c: (c[0].coords[0][1], c[0].coords[0][0]))

    ordered = []
    for cell in cells:
        for i, seg in enumerate(cell):
            ordered.append(LineString(seg.coords[::-1]) if i % 2 else seg)
    return ordered


def _group_rows(segments) -> list[list[LineString]]:
    """Segments bucketed by sweep offset, bottom row first, each row
    sorted along the flight direction."""
    rows: dict[float, list[LineString]] = {}
    for seg in segments:
        rows.setdefault(round(seg.coords[0][1], 6), []).append(seg)
    return [sorted(rows[y], key=lambda s: s.coords[0][0]) for y in sorted(rows)]


def _build_cells(rows) -> list[list[LineString]]:
    """Group segments into cells: walk the rows bottom-to-top, linking each segment to the one below it
    when their along-line spans overlap. A row that splits into several
    segments (two arms, or around a hole) starts new cells; several
    segments merging back start a single one."""
    finished: list[list[LineString]] = []
    open_cells: list[list[LineString]] = []
    open_span: list[tuple[float, float]] = []  # along-line span of each open cell's last segment

    for row in rows:
        spans = [(s.coords[0][0], s.coords[-1][0]) for s in row]
        prev_hits = [[] for _ in open_cells]  # cur indices overlapping each open cell
        cur_hits = [[] for _ in row]          # open cell indices overlapping each cur segment
        for k, (px0, px1) in enumerate(open_span):
            for j, (cx0, cx1) in enumerate(spans):
                if px0 <= cx1 and cx0 <= px1:
                    prev_hits[k].append(j)
                    cur_hits[j].append(k)

        next_cells: list[list[LineString]] = []
        next_span: list[tuple[float, float]] = []
        carried = set()
        for k, cell in enumerate(open_cells):
            hits = prev_hits[k]
            if len(hits) == 1 and len(cur_hits[hits[0]]) == 1:  # plain continuation
                j = hits[0]
                cell.append(row[j])
                next_cells.append(cell)
                next_span.append(spans[j])
                carried.add(j)
            else:  # split, merge, or dead end
                finished.append(cell)

        for j, seg in enumerate(row):  # in-events, split children, merge results
            if j not in carried:
                next_cells.append([seg])
                next_span.append(spans[j])

        open_cells, open_span = next_cells, next_span

    finished.extend(open_cells)
    return finished


# def route_transits(lines, polygon, restricted) -> list[LineString]:
#     """One transit leg per consecutive line pair, in the projected CRS.
#     Straight hop unless restricted and the hop leaves the polygon,
#     then walk along the boundary instead."""
#     safe = polygon.buffer(0.5)
#     ring = polygon.exterior
#     transits = []
#     for prev, nxt in zip(lines, lines[1:]):
#         hop = LineString([prev.coords[-1], nxt.coords[0]])
#         if restricted and not hop.covered_by(safe):
#             hop = _boundary_path(ring, hop.coords[0], hop.coords[-1])
#             if not hop.covered_by(safe):
#                 raise ValueError(
#                     "restricted transit still leaves the AOI; the boundary "
#                     "walk cannot route around holes")
#         transits.append(hop)
#     return transits


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
