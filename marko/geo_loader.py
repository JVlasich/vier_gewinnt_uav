import os
import json
from shapely.geometry import shape

def load_geojson(filepath):
    base_dir = os.path.dirname(__file__)
    full_path = os.path.join(base_dir, filepath)

    with open(full_path, "r") as f:
        data = json.load(f)

    return shape(data["features"][0]["geometry"])