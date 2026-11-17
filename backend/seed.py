"""Idempotent seed: warehouse layout, connections, and small demo inventory.

Layout (approved): RECEIVING (0,1) non-storage + 3x3 shelves A1-C3 with
capacities of only 30 / 50 / 100. Connections are grid adjacency stored in
both directions. A2<->B2 starts blocked; alternative routes exist via
A1-B1-B2 or A3-B3-B2.
"""
from backend.models import Location, WarehouseConnection

LAYOUT = [
    # code, row, column, max_capacity
    ("RECEIVING", 0, 1, 0),
    ("A1", 1, 0, 50),
    ("A2", 1, 1, 30),
    ("A3", 1, 2, 100),
    ("B1", 2, 0, 100),
    ("B2", 2, 1, 50),
    ("B3", 2, 2, 30),
    ("C1", 3, 0, 30),
    ("C2", 3, 1, 100),
    ("C3", 3, 2, 50),
]

BLOCKED_PAIRS = {frozenset(("A2", "B2"))}

DEMO_INVENTORY = [("Keyboard", 10), ("Mouse", 15), ("USB Cable", 20)]


def seed_database(db):
    if db.query(Location).count() > 0:
        return  # already seeded — idempotent

    locations = {}
    for code, row, col, capacity in LAYOUT:
        loc = Location(
            location_code=code,
            row_number=row,
            column_number=col,
            max_capacity=capacity,
            occupied_capacity=0,
            is_active=True,
        )
        db.add(loc)
        locations[code] = loc
    db.flush()

    by_coord = {(row, col): code for code, row, col, _cap in LAYOUT}
    pairs = set()
    for code, row, col, _cap in LAYOUT:
        for d_row, d_col in ((0, 1), (1, 0)):  # right and down neighbours only
            neighbour = by_coord.get((row + d_row, col + d_col))
            if neighbour:
                pairs.add((code, neighbour))
    for src_code, dst_code in sorted(pairs):
        blocked = frozenset((src_code, dst_code)) in BLOCKED_PAIRS
        for a, b in ((src_code, dst_code), (dst_code, src_code)):
            db.add(
                WarehouseConnection(
                    source_location_id=locations[a].location_id,
                    destination_location_id=locations[b].location_id,
                    distance=1.0,
                    is_blocked=blocked,
                )
            )
    db.commit()

    # Demo stock goes through the real allocation service so inventory,
    # occupied capacity and movement history are all consistent.
    from backend.services.allocation_service import store_product

    for product_name, quantity in DEMO_INVENTORY:
        store_product(db, product_name, quantity)
