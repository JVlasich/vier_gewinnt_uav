def lines_to_waypoints(lines, altitude):
    waypoints = []
    reverse = False

    for line in lines:
        coords = list(line.coords)

        # Zick-Zack umkehren
        if reverse:
            coords = coords[::-1]

        for x, y in coords:
            waypoints.append({
                "lat": y,
                "lon": x,
                "alt": altitude
            })

        reverse *= -1 # reverse = not reverse

    return waypoints