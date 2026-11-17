"""Stock dispatch: atomic removal across locations.

Deterministic order: locations sorted by Manhattan distance from RECEIVING,
tie-break by location_code. Either the whole dispatch succeeds or nothing
changes. Movement history is always preserved; inventory rows that reach
zero are removed.
"""
from backend.algorithms.heuristic import manhattan_distance
from backend.config import START_LOCATION
from backend.models import Inventory, Location, StockMovement
from backend.services.allocation_service import get_product_by_name
from backend.services.errors import AppError


def dispatch_product(db, product_name, quantity):
    name = (product_name or "").strip()
    if not name:
        raise AppError("Product name must not be empty", "VALIDATION_ERROR", 422)
    if quantity is None or quantity <= 0:
        raise AppError("Quantity must be greater than zero", "VALIDATION_ERROR", 422)

    product = get_product_by_name(db, name)
    if product is None:
        raise AppError(f"Product '{name}' not found", "PRODUCT_NOT_FOUND", 404)

    rows = (
        db.query(Inventory)
        .filter(Inventory.product_id == product.product_id)
        .all()
    )
    total_available = sum(r.quantity for r in rows)
    if total_available < quantity:
        raise AppError(
            f"Insufficient stock: requested {quantity}, available {total_available}",
            "INSUFFICIENT_STOCK",
            409,
        )

    receiving = db.query(Location).filter(Location.location_code == START_LOCATION).first()

    def sort_key(row):
        loc = row.location
        distance = manhattan_distance(
            loc.row_number, loc.column_number,
            receiving.row_number, receiving.column_number,
        )
        return (distance, loc.location_code)

    rows.sort(key=sort_key)

    try:
        remaining_to_take = quantity
        affected = []
        for row in rows:
            if remaining_to_take == 0:
                break
            take = min(row.quantity, remaining_to_take)
            row.quantity -= take
            row.location.occupied_capacity -= take
            db.add(
                StockMovement(
                    product_id=product.product_id,
                    location_id=row.location_id,
                    movement_type="OUT",
                    quantity=take,
                )
            )
            affected.append(
                {
                    "location": row.location.location_code,
                    "quantity_dispatched": take,
                    "remaining_at_location": row.quantity,
                }
            )
            if row.quantity == 0:
                db.delete(row)
            remaining_to_take -= take
        db.commit()
    except Exception:
        db.rollback()
        raise

    return {
        "product": product.name,
        "quantity_dispatched": quantity,
        "remaining_stock": total_available - quantity,
        "locations_affected": affected,
    }
