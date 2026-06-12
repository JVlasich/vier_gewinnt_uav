# type: ignore # RREMOVE WHEN STARTING PROGRAMMING HERE
"""Python Module for computing metrics for a created flight plan"""

from .types import MissionParams, Metrics

def swath_width(altitude_m, fov_deg) -> float:
    pass # 2·h·tan(fov/2)

def line_spacing(swath_m, overlap) -> float:
    pass # W·(1−o)

def point_density(prf_hz, swath_m, speed_ms, overlap) -> float:
    pass

def along_track_spacing(speed_ms, scan_line_rate_hz) -> float:
    pass

def max_speed_for_spacing(scan_line_rate_hz, target_m) -> float:
    pass

def validate(params: MissionParams) -> list[str]:
    pass # range checks → warnings

def compute_metrics(params, lines, crs_epsg) -> Metrics:
    pass