from simplekml import Kml

def export_waypoints(waypoints, filename):
    kml = Kml()

    for wp in waypoints:
        kml.newpoint(coords=[(wp.lon, wp.lat)])

    kml.save(filename)