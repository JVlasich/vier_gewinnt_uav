# routing.py
"""Transit routing between flight lines. In restricted mode illegal
transits are replaced by the shortest path inside the AOI, found with
Dijkstra on a visibility graph over the polygon vertices.

simple drop in alternative: geometry.route_transits"""

import heapq
import math

from shapely.geometry import LineString, Polygon

EPS = 0.5  # m, legality tolerance


class _VisibilityRouter:
    def __init__(self, polygon: Polygon):
        self.safe = polygon.buffer(EPS)
        self.nodes = []
        for ring in [polygon.exterior, *polygon.interiors]:
            self.nodes.extend(ring.coords[:-1])  # drop closing duplicate

        # vertex-to-vertex visibility, built once per mission
        self.adj: dict[int, list[tuple[int, float]]] = {i: [] for i in range(len(self.nodes))}
        for i in range(len(self.nodes)):
            for j in range(i + 1, len(self.nodes)):
                if self._visible(self.nodes[i], self.nodes[j]):
                    d = math.dist(self.nodes[i], self.nodes[j])
                    self.adj[i].append((j, d))
                    self.adj[j].append((i, d))

    def _visible(self, a, b) -> bool:
        return LineString([a, b]).covered_by(self.safe)

    def route(self, p0, p1) -> list[tuple[float, float]]:
        if self._visible(p0, p1):
            return [p0, p1]

        # temporary nodes for this query, on a copy of the adjacency
        start, end = len(self.nodes), len(self.nodes) + 1
        points = self.nodes + [p0, p1]
        adj = {i: list(edges) for i, edges in self.adj.items()}
        adj[start] = []
        adj[end] = []
        for i, node in enumerate(self.nodes):
            for temp, p in ((start, p0), (end, p1)):
                if self._visible(p, node):
                    d = math.dist(p, node)
                    adj[temp].append((i, d))
                    adj[i].append((temp, d))

        path = _dijkstra(adj, start, end)
        if path is None:
            raise ValueError(
                f"no transit path inside the AOI from {p0} to {p1}; pinched polygon?")
        return [points[i] for i in path]


def _dijkstra(adj, start, end) -> list[int] | None:
    best = {start: 0.0}
    prev = {start: None}
    queue = [(0.0, start)]
    done = set()
    while queue:
        dist, node = heapq.heappop(queue)
        if node in done:
            continue
        done.add(node)
        if node == end:
            path = []
            while node is not None:
                path.append(node)
                node = prev[node]
            return path[::-1]
        for neighbor, weight in adj[node]:
            new_dist = dist + weight
            if new_dist < best.get(neighbor, float("inf")):
                best[neighbor] = new_dist
                prev[neighbor] = node
                heapq.heappush(queue, (new_dist, neighbor))
    return None


def route_transits(lines, polygon, restricted) -> list[LineString]:
    """One transit leg per consecutive line pair, in the projected CRS."""
    router = _VisibilityRouter(polygon) if restricted else None
    transits = []
    for prev, nxt in zip(lines, lines[1:]):
        p0, p1 = prev.coords[-1], nxt.coords[0]
        if router is not None:
            transits.append(LineString(router.route(p0, p1)))
        else:
            transits.append(LineString([p0, p1]))
    return transits
