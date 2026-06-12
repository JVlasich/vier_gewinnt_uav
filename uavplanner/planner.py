from .planner_types import MissionParams, FlightPlan

# planner.py
def plan_mission(polygon_wgs84, params: MissionParams) -> FlightPlan:
    pass
    # validate → project → spacing → strategy → unproject
    # → build FlightPlan → compute_metrics → return