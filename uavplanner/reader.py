import json
from pathlib import Path
from typing import Callable

from shapely.geometry import shape

_readers: dict[str, Callable] = {}  # ".geojson" -> reader fn


def register_reader(*extensions: str):
    def decorator(fn):
        for ext in extensions:
            _readers[ext.lower()] = fn
        return fn

    return decorator


def read_polygon(path: str):
    """Dispatch on extension. Always returns a WGS84 (lon, lat) polygon."""
    ext = Path(path).suffix.lower()
    try:
        return _readers[ext](path)
    except KeyError:
        raise ValueError(f"no reader for {ext}; have {list(_readers)}")


@register_reader(".geojson", ".json")
def read_geojson(path: str):

    with open(path, "r") as f:
        data = json.load(f)

    return shape(data["features"][0]["geometry"])


# TODO: Space here for future readers (.shp, txt, ...)

if __name__ == "__main__":
    print(read_polygon("test_polygon_austria.geojson"))
