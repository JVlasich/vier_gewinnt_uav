"""Python Module for computing metrics for a created flight plan"""

import math

from .planner_types import Metrics, MissionParams


def swath_width(altitude_m, fov_deg) -> float:
    return 2 * altitude_m * math.tan(math.radians(fov_deg) / 2)


def line_spacing(swath_m, overlap) -> float:
    return swath_m * (1 - overlap)


def point_density(prf_hz, swath_m, speed_ms, overlap) -> float:
    return prf_hz / (swath_m * speed_ms) / (1 - overlap)


def validate(params: MissionParams) -> list[str]:
    if params.altitude <= 0:
        raise ValueError(f"altitude must be > 0, got {params.altitude}")
    if params.velocity <= 0:
        raise ValueError(f"velocity must be > 0, got {params.velocity}")
    if not 0 < params.fov < 180:
        raise ValueError(f"fov must be in (0, 180) degrees, got {params.fov}")
    if not 0 <= params.overlap < 1:
        raise ValueError(f"overlap must be in [0, 1), got {params.overlap}")
    if params.lead_in < 0:
        raise ValueError(f"lead_in must be >= 0, got {params.lead_in}")
    if params.restricted and params.lead_in > 0:
        raise ValueError("lead_in extends lines beyond the AOI, not allowed with restricted")

    warnings = []
    if params.altitude > 120:
        warnings.append(
            f"altitude {params.altitude} m exceeds typical 120 m legal limit"
        )
    return warnings


def compute_metrics(params: MissionParams, lines, transits) -> Metrics:
    """lines and transits are projected shapely LineStrings"""
    swath = swath_width(params.altitude, params.fov)
    spacing = line_spacing(swath, params.overlap)
    density = None
    if params.prf is not None:
        density = point_density(params.prf, swath, params.velocity, params.overlap)

    total = sum(line.length for line in lines) + sum(t.length for t in transits)

    return Metrics(
        swath=swath,
        line_spacing=spacing,
        num_lines=len(lines),
        azimuth=params.flight_azimuth,
        point_density=density,
        total_length=total,
        est_duration=total / params.velocity,
        warnings=validate(params),
    )
