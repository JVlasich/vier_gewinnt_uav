"""Plot a mission KML against its AOI polygon."""

import argparse
import xml.etree.ElementTree as ET

import matplotlib.pyplot as plt

from uavplanner.reader import read_polygon

KML_NS = {"kml": "http://www.opengis.net/kml/2.2"}


def read_kml(path):
    """Returns (waypoints, path): waypoints as [(name, lon, lat)],
    path as [(lon, lat)]."""
    root = ET.parse(path).getroot()
    waypoints = []
    track = []
    for pm in root.iter("{http://www.opengis.net/kml/2.2}Placemark"):
        name = pm.findtext("kml:name", default="", namespaces=KML_NS)
        point = pm.find("kml:Point/kml:coordinates", KML_NS)
        line = pm.find("kml:LineString/kml:coordinates", KML_NS)
        if point is not None:
            lon, lat = point.text.strip().split(",")[:2]
            waypoints.append((name, float(lon), float(lat)))
        elif line is not None:
            for entry in line.text.split():
                lon, lat = entry.split(",")[:2]
                track.append((float(lon), float(lat)))
    return waypoints, track


def plot(waypoints, track, polygon, title):
    fig, ax = plt.subplots(figsize=(9, 9))

    x, y = polygon.exterior.xy
    ax.fill(x, y, color="lightgreen", alpha=0.5, zorder=1)
    ax.plot(x, y, color="green", lw=1.5, label="AOI", zorder=2)

    if track:
        tx = [p[0] for p in track]
        ty = [p[1] for p in track]
        ax.plot(tx, ty, color="crimson", lw=1.5, label="flight path", zorder=3)
        for (x0, y0), (x1, y1) in zip(track, track[1:]):
            ax.annotate("", xy=((x0 + x1) / 2, (y0 + y1) / 2), xytext=(x0, y0),
                        arrowprops=dict(arrowstyle="-|>", color="crimson", lw=1.5),
                        zorder=4)

    for name, lon, lat in waypoints:
        ax.plot(lon, lat, "o", color="navy", ms=6, zorder=5)
        ax.annotate(name, (lon, lat), textcoords="offset points",
                    xytext=(6, 6), color="navy", fontsize=9, zorder=5)

    ax.set_aspect("equal")
    ax.set_xlabel("longitude")
    ax.set_ylabel("latitude")
    ax.set_title(title)
    ax.legend(loc="upper right")
    ax.ticklabel_format(useOffset=False)
    fig.tight_layout()
    return fig


def main():
    p = argparse.ArgumentParser(description="Plot a mission KML over its AOI polygon.")
    p.add_argument("kml", help="mission KML file")
    p.add_argument("polygon", help="AOI polygon file (.geojson/.json)")
    p.add_argument("-o", "--output", default=None,
                   help="save plot as image instead of showing it")
    args = p.parse_args()

    waypoints, track = read_kml(args.kml)
    polygon = read_polygon(args.polygon)
    fig = plot(waypoints, track, polygon, args.kml)

    if args.output:
        fig.savefig(args.output, dpi=150)
        print(f"wrote {args.output}")
    else:
        plt.show()


if __name__ == "__main__":
    main()
