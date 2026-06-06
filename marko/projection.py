from pyproj import Transformer
from shapely.ops import transform

# Wien = UTM Zone 33N
transformer = Transformer.from_crs(
    "EPSG:4326",   # WGS84 (lon/lat)
    "EPSG:32633",  # UTM 33N (Meter)
    always_xy=True
)

def to_utm(geom):
    return transform(transformer.transform, geom)