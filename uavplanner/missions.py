# missions/__init__.py
from typing import Callable
from .planner_types import LineString

_missions: dict[str, Callable] = {}    # the registry: name -> function

def register(name: str):
    """Decorator factory: returns a decorator that files fn under name."""
    def decorator(fn):
        _missions[name] = fn           # register the function in the dict
        return fn                      # nothing ever happens
    return decorator

def get_strategy(name: str) -> Callable:
    try:
        return _missions[name]
    except KeyError:
        raise ValueError(f"unknown mission type {name}; we have {list(_missions)}")



@register("single_grid")
def single_grid(polygon_proj, params, spacing_m) -> list["LineString"]:
    pass