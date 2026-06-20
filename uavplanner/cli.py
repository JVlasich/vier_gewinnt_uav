# cli.py
import argparse

from .planner import plan_mission
from .planner_types import MissionParams
from .reader import read_polygon
from .writer import write_kml


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="uavplanner",
        description="Create UAV-LiDAR flight plans (waypoint KML) from an AOI polygon.",
    )
    p.add_argument("input", help="AOI polygon file (.geojson/.json)")
    p.add_argument("-o", "--output", default="mission.kml", help="output KML path")
    p.add_argument("--altitude", type=float, required=True, help="flying altitude [m]")
    p.add_argument("--velocity", type=float, required=True, help="flight speed [m/s]")
    p.add_argument("--fov", type=float, required=True, help="scanner FOV, full angle [deg]")
    p.add_argument("--azimuth", type=float, default=0.0, help="main flight direction [deg clockwise from north]",)
    p.add_argument("--overlap", type=float, default=0.3, help="swath overlap, fraction 0..1")
    p.add_argument("--lead-in", type=float, default=0.0, help="line extension on both ends [m]")
    p.add_argument("--mission", default="single_grid", choices=["single_grid", "double_grid"], help="mission type",)
    p.add_argument("--prf", type=float, default=None, help="pulse repetition frequency [Hz], enables point density estimate",)
    p.add_argument("--epsg", type=int, default=None, help="projected EPSG code (default: auto UTM zone)",)
    p.add_argument("--restricted", action="store_true", help="keep transits inside the AOI (no-fly outside)")
    return p


def main(argv=None) -> None:
    args = build_parser().parse_args(argv)

    params = MissionParams(
        altitude=args.altitude,
        velocity=args.velocity,
        fov=args.fov,
        flight_azimuth=args.azimuth,
        overlap=args.overlap,
        lead_in=args.lead_in,
        epsg=args.epsg,
        prf=args.prf,
        mission_type=args.mission,
        restricted=args.restricted,
    )

    polygon = read_polygon(args.input)
    plan = plan_mission(polygon, params)
    m = plan.metrics

    print(f"mission type:         {params.mission_type}")
    print(f"projected CRS:        EPSG:{plan.crs_epsg}")
    print(f"swath width:          {m.swath:.1f} m")
    print(f"line spacing:         {m.line_spacing:.1f} m")
    print(f"flight lines:         {m.num_lines}")
    if m.point_density is not None:
        print(f"point density:        {m.point_density:.1f} pts/m^2")
    print(f"total length:         {m.total_length:.0f} m")
    print(f"est. duration:        {m.est_duration / 60:.1f} min")
    for w in m.warnings:
        print(f"WARNING: {w}")

    write_kml(plan, args.output)
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
