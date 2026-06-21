# Ich mach morgen weiter, mein Kopf tut weh, ich hab vergessen in der Uni zu speichern :(((((((((((
# UAV-LiDAR flight planning tool
A project written for the course Python-Programmierung für Geowissenschaften [120.113] @ TU Wien  
## Aim of the Project
The task  was to implement a simple tool to create flight plans for UAV-LiDAR surveys.  
The tool should take an area-of-interest polygon and basic flight mission parameters (flying altitude. flight speed, scanner FOV, scan rate, main flight direction, mission type...) as input and should return a waypoint kml file (readable for DJI pilot app) as output.  
The tool should be available as a  python module including an argument parser for execution from a command shell.  
In addition, implementation as a a simple QGIS plugin is desired.
## Features
1) Input: an AOI polygon, given as a GeoJSON file (.geojson/.json).
2) Planning: the polygon is projected into a local metric coordinate system (UTM, auto-detected from the AOI's location unless an EPSG code is given) and flight lines are generated according to the chosen mission type:
  single_grid – a back-and-forth raster across the AOI.
  double_grid – two rasters at 90° to each other for denser coverage.
  corridor – follows the centerline of a long, narrow AOI (road, river, ...) instead of a straight raster, the flight tracks bends in the corridor supports multiple parallel lines if the corridor is wider than one sensor swath.
3) Metrics: swath width, line spacing, number of lines, estimated point density, total flight length and flight duration are computed and printed to the console.
4) Output: the flight plan is exported as a KML file containing numbered waypoint placemarks and the full flight path as a line.
## Installation
Requires Python 3.10+
## Usage
input: (positional)AOI polygon file (.geojson/.json)  
-o/--output: Output KML path (default: mission.kml)  
--altitude: Flying altitude in meters (required)  
--velocity: Flight speed in m/s (required)  
--fovScanner: field of view, full angle in degrees (required)  
--azimuth: Main flight direction in degrees clockwise from north or auto (default) to pick the shortest path automatically  
--overlap: Swath overlap as a fraction 0–1 (default: 0.3)  
--lead-in: Line extension on both ends in meters, for sensor warm-up (default: 0)  
--mission: Mission type: single_grid, double_grid, or corridor (default: single_grid)  
--prfPulse repetition frequency in Hz, if given, enables a point density estimate  
--epsg: Projected EPSG code to use (default: automatically picked UTM zone)  
--restricted: Keep transit paths between flight lines inside the AOI (no flying outside the polygon) 
## Structure
```
uavplanner/
├── __init__.py : Marks uavplanner as a Python package
├── __main__.py :  Imports and calls cli.main()
├── cli.py : Command-line argument parsing and console output
├── crs.py : Coordinate reference system handling (WGS84, projected UTM)
├── geometry.py : Core raster flight-line generation, automatic azimuth optimization, transit routing
├── metrics.py : Swath width, line spacing, point density, and parameter validation
├── missions.py : Mission type registry
├── planner_types.py : Data structures(MissionParams, Waypoint, FlightLine, Metrics, FlightPlan)
├── planner.py : Responsible for (validate, project, generate lines, route transits, compute metrics, export)
├── reader.py : AOI file readers (GeoJSON, plain-text coordinate lists)
├── routing.py : Handles AOIs with holes (JULES FRAGEN)
├── test.py : Testenviroment
└── writer.py : KML export
```
## Examples
Bilder
## Trivia
Longitude and Latitude made us sad:(
Without Dijkstra-Algorithm the drone flies mad. 
## Test
