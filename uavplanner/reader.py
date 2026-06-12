import json
from pathlib import Path
from typing import Callable
from shapely.geometry import Polygon
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
@register_reader(".txt")
def read_txt(path: str):
    """Reads a text file with coordinates: lon,lat per line"""
    coords = []

    with open(path, "r") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            if line.startswith("#"):
                continue

            lon_str, lat_str = line.split(",")

            lon = float(lon_str.strip())
            lat = float(lat_str.strip())

            coords.append((lon, lat))

    if coords[0] != coords[-1]:
        coords.append(coords[0])

    return Polygon(coords)

if __name__ == "__main__":
    print(read_polygon("test_polygon_austria.geojson"))
