"""Builds an in-memory graph snapshot of the warehouse from the database.

A pathway counts as blocked if EITHER direction row is blocked, so blocked
edges are simply omitted from the adjacency used by the search algorithms.
"""
from backend.models import Location, WarehouseConnection


def build_graph(db):
    locations = db.query(Location).all()
    nodes = {}
    by_id = {}
    for loc in locations:
        nodes[loc.location_code] = {
            "row": loc.row_number,
            "column": loc.column_number,
            "max_capacity": loc.max_capacity,
            "occupied_capacity": loc.occupied_capacity,
            "remaining_capacity": loc.remaining_capacity,
            "is_active": loc.is_active,
        }
        by_id[loc.location_id] = loc.location_code

    connections = db.query(WarehouseConnection).all()
    blocked_pairs = set()
    for conn in connections:
        if conn.is_blocked:
            pair = frozenset(
                (by_id[conn.source_location_id], by_id[conn.destination_location_id])
            )
            blocked_pairs.add(pair)

    adjacency = {code: [] for code in nodes}
    seen = set()
    for conn in connections:
        src = by_id[conn.source_location_id]
        dst = by_id[conn.destination_location_id]
        if frozenset((src, dst)) in blocked_pairs:
            continue
        key = (src, dst)
        if key in seen:
            continue
        seen.add(key)
        adjacency[src].append((dst, conn.distance))
    for code in adjacency:
        adjacency[code].sort(key=lambda item: item[0])
    return {"nodes": nodes, "adjacency": adjacency}
