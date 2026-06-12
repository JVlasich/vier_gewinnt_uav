# type: ignore # RREMOVE WHEN STARTING PROGRAMMING HERE
# crs.py
from shapely.geometry import Polygon
from shapely.ops import transform
from pyproj import CRS, Transformer
import math

def pick_utm_epsg(polygon_wgs84: Polygon) -> int:
    centroid = (polygon_wgs84.centroid.x, polygon_wgs84.centroid.y)
    utm_zone = math.floor((centroid[1] + 180) / 6) + 1
    utm_crs = CRS.from_user_input(f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs")
    print(utm_crs)
    utm_epsg = utm_crs.to_epsg()
    return utm_epsg


def to_projected(polygon_wgs84: Polygon, epsg: int) -> Polygon:
    transformer = Transformer.from_crs(
    crs_from=4326, 
    crs_to=epsg, 
    always_xy=True
    )

    return transform(transformer.transform, polygon_wgs84)

# def to_wgs84(coords, epsg) -> list[tuple[float, float]]:
#     transformer = Transformer.from_crs(
#     crs_from=epsg, 
#     crs_to=4326, 
#     always_xy=True
#     )

#     return transformer.transform(coords[0], coords[1]) # lat, lon -> lon, lat

def to_wgs84(polygon_projected: Polygon, epsg: int) -> Polygon:
    transformer = Transformer.from_crs(
    crs_from=epsg, 
    crs_to=4326, 
    always_xy=True
    )

    return transform(transformer.transform, polygon_projected)

if __name__ == "__main__":
    from shapely.geometry import Polygon
    poly = Polygon([(48.083978, 16.392753), (48.084, 16.392), (48.084, 16.393)])
    epsg = pick_utm_epsg(poly)
    print(f"UTM EPSG code: {epsg}")

    projected = to_projected(poly, epsg) 
    print(projected)

    # wgs84 = [to_wgs84((x,y),epsg) for x,y in projected.exterior.coords]
    wgs84 = to_wgs84(projected, epsg)
    print(wgs84)

    # lat lon make sad 😞

