from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom


def export_kml(waypoints, filename="mission.kml"):
    kml = Element("kml", xmlns="http://www.opengis.net/kml/2.2")
    doc = SubElement(kml, "Document")

    for i, wp in enumerate(waypoints):
        pm = SubElement(doc, "Placemark")

        name = SubElement(pm, "name")
        name.text = f"WP{i+1}"

        point = SubElement(pm, "Point")

        coords = SubElement(point, "coordinates")
        coords.text = f"{wp['lon']},{wp['lat']},{wp['alt']}"

    # hübsch formatieren
    rough = tostring(kml, "utf-8")
    reparsed = minidom.parseString(rough)
    pretty = reparsed.toprettyxml(indent="  ")

    with open(filename, "w", encoding="utf-8") as f:
        f.write(pretty)

    print(f"KML gespeichert: {filename}")