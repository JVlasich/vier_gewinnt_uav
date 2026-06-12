# geometry.py
def generate_flight_lines(polygon_proj, spacing_m, azimuth_deg,
                          lead_in_m=0.0) -> list["LineString"]:
    # _rotate(...)            → align azimuth to an axis
    # _slice_bbox(...)        → horizontal lines spaced S apart
    # _clip_to_polygon(...)   → keep the inside segments
    # _order_boustrophedon(.) → alternate direction
    # then rotate back