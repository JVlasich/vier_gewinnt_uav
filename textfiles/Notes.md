# Definitions

## Flight Azimuth
- compass bearing of your main flight lines: the direction the drone
  flies the long passes, in degrees clockwise from north
  (0° = N, 90° = E).
- footgun: Trig functions use normal degrees or rad not azimuth
  -> have to rotate

## Waypoint
- a position (lat, lon), an altitude, and optional per-point parameters
  (speed, heading, gimbal angle, "start/stop recording", hover, turn style)
- Mission: ordered list of waypoints plus global settings, and the autopilot
  flies straight segments between consecutive ones.

# Parameters

## Across-Track
- Swath
    W = 2 · h · tan(FOV/2)
- Overlap
    S = W · (1 − o)
    mit o...Prozent Overlap, S...spacing

## Along-Track
- Spacing
    v / f
    mit v...geschwindigkeit, f...scan-line-rate (Hz,sweeps/s)
    Problem mit f: osciallating/rotating mirror vs. Risley prism
- Pulse-rate
    Hz, Point-per-second

## Density
- D ≈ PRF / (W · v)
- overlap increases D by: 1/(1-o)

## Flight-direction
- doesnt affect density on flat ground
- Pick to waste less battery turning and handle oclusion/terrain

## Mission types
- Single grid is one parallel set (simple)
- Double grid / crosshatch is two perpendicular sets (urban/forest)
- Corridor is 1-3 lines following a linear feature (road,river)
- terrain following is independent of the others
  and keeps W and D kosntant by adjusting altitue 

## Implication
flying higher and faster both make the mission cheaper
(wider swath = fewer lines; faster = less air time)
but both thin density, and altitude additionally costs
ranging accuracy and a bigger beam footprint

# Architecture
- a geometry layer that places lines and waypoints;
  consumes altitude, FOV, overlap, AOI, azimuth, mission type;
- a metrics/validation layer that reports on the plan;
  consumes speed, PRF, and (optionally) scan rate to compute density,
  along-track spacing, and mission duration, and to flag problems.

## Main Algorythm
- (1) Rotate the polygon about its centroid by −azimuth,
  so the flight direction lands on the x-axis
  and flight lines become plain horizontal lines
- (2) take the bounding box of the rotated polygon
  and lay horizontal lines across it,
  spaced S apart (offset the first by S/2 so none sits exactly on an edge).
- (3) intersect each line with the polygon and keep only the part inside 
- (4) order the lines and flip direction every other one
  (left-right, then right-left…) so each line ends near the next one's start
- (5) Undo rotation

## Probable files
- planner.py
- metrics.py
- missions.py
- writer.py
- cli.py

## dependencies
- shapely
- pyproj
- simplekml

# QGIS
- Python package dropped in the user's profile under python/plugins/<yourplugin>/
- metadata.txt (name, version, qgisMinimumVersion)
- __init__.py exposing classFactory(iface). QGIS calls that, gets plugin object, and calls its initGui() (where a toolbar button or menu entry is added) and unload() (cleanup).
- How to build: QgsProcessingAlgorithm 