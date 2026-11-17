"""Warehouse reads: locations, capacity, map, and connection blocking."""
from backend.models import Location, WarehouseConnection
from backend.services.errors import AppError


def location_to_dict(loc):
    return {
        "location_id": loc.location_id,
        "location_code": loc.location_code,
        "max_capacity": loc.max_capacity,
        "occupied_capacity": loc.occupied_capacity,
        "remaining_capacity": loc.remaining_capacity,
        "row_number": loc.row_number,
        "column_number": loc.column_number,
        "is_active": loc.is_active,
        "is_storage": loc.max_capacity > 0,
    }


def list_locations(db):
    locs = db.query(Location).order_by(Location.location_id).all()
    return [location_to_dict(loc) for loc in locs]


def get_location(db, location_code):
    loc = (
        db.query(Location)
        .filter(Location.location_code == location_code.strip().upper())
        .first()
    )
    if loc is None:
        raise AppError(f"Location '{location_code}' not found", "LOCATION_NOT_FOUND", 404)
    data = location_to_dict(loc)
    conns = (
        db.query(WarehouseConnection)
        .filter(WarehouseConnection.source_location_id == loc.location_id)
        .all()
    )
    by_id = {item.location_id: item.location_code for item in db.query(Location).all()}
    data["connections"] = [
        {
            "connection_id": c.connection_id,
            "to": by_id.get(c.destination_location_id),
            "distance": c.distance,
            "is_blocked": c.is_blocked,
        }
        for c in conns
    ]
    return data


def warehouse_map(db):
    locations = db.query(Location).all()
    by_id = {loc.location_id: loc.location_code for loc in locations}
    edges = {}
    for conn in db.query(WarehouseConnection).all():
        src = by_id[conn.source_location_id]
        dst = by_id[conn.destination_location_id]
        key = tuple(sorted((src, dst)))
        if key not in edges:
            edges[key] = {
                "connection_id": conn.connection_id,
                "source": key[0],
                "destination": key[1],
                "distance": conn.distance,
                "is_blocked": conn.is_blocked,
            }
        elif conn.is_blocked:
            edges[key]["is_blocked"] = True
    return {"nodes": [location_to_dict(loc) for loc in locations],
            "edges": sorted(edges.values(), key=lambda e: (e["source"], e["destination"]))}


def capacity_summary(db):
    locs = db.query(Location).all()
    storage = [loc for loc in locs if loc.max_capacity > 0]
    return {
        "total_locations": len(locs),
        "storage_locations": len(storage),
        "total_capacity": sum(loc.max_capacity for loc in storage),
        "total_occupied": sum(loc.occupied_capacity for loc in storage),
        "total_remaining": sum(loc.remaining_capacity for loc in storage),
        "locations": [location_to_dict(loc) for loc in storage],
    }


def set_connection_blocked(db, connection_id, is_blocked):
    conn = (
        db.query(WarehouseConnection)
        .filter(WarehouseConnection.connection_id == connection_id)
        .first()
    )
    if conn is None:
        raise AppError("Connection not found", "CONNECTION_NOT_FOUND", 404)
    # Update BOTH directions in one transaction so a pathway is never half-open.
    pair = db.query(WarehouseConnection).filter(
        (
            (WarehouseConnection.source_location_id == conn.source_location_id)
            & (WarehouseConnection.destination_location_id == conn.destination_location_id)
        )
        | (
            (WarehouseConnection.source_location_id == conn.destination_location_id)
            & (WarehouseConnection.destination_location_id == conn.source_location_id)
        )
    ).all()
    try:
        for row in pair:
            row.is_blocked = is_blocked
        db.commit()
    except Exception:
        db.rollback()
        raise
    by_id = {loc.location_id: loc.location_code for loc in db.query(Location).all()}
    return {
        "connection_id": conn.connection_id,
        "source": by_id[conn.source_location_id],
        "destination": by_id[conn.destination_location_id],
        "is_blocked": is_blocked,
        "updated_rows": len(pair),
    }
