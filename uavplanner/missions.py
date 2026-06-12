# missions.py
from typing import Callable
from shapely.geometry import LineString

from .geometry import generate_flight_lines

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
