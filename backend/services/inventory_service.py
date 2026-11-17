"""Inventory reads: listing, per-product locations, locate / fulfilment check."""
from backend.models import Inventory, Product
from backend.services.allocation_service import get_product_by_name
from backend.services.errors import AppError


def inventory_row_to_dict(row):
    return {
        "product": row.product.name,
        "product_id": row.product_id,
        "location": row.location.location_code,
        "location_id": row.location_id,
        "quantity": row.quantity,
        "updated_at": row.updated_at.isoformat() if row.updated_at else None,
    }


def list_inventory(db):
    rows = db.query(Inventory).order_by(Inventory.product_id, Inventory.location_id).all()
    return [inventory_row_to_dict(r) for r in rows]


def inventory_for_product(db, product_id):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if product is None:
        raise AppError("Product not found", "PRODUCT_NOT_FOUND", 404)
    rows = (
        db.query(Inventory)
        .filter(Inventory.product_id == product_id)
        .order_by(Inventory.location_id)
        .all()
    )
    return {
        "product": product.name,
        "product_id": product.product_id,
        "total_quantity": sum(r.quantity for r in rows),
        "locations": [inventory_row_to_dict(r) for r in rows],
    }


def locate_product(db, product_name, requested_quantity):
    name = (product_name or "").strip()
    if not name:
        raise AppError("Product name must not be empty", "VALIDATION_ERROR", 422)
    if requested_quantity is None or requested_quantity <= 0:
        raise AppError("Requested quantity must be greater than zero", "VALIDATION_ERROR", 422)
    product = get_product_by_name(db, name)
    if product is None:
        raise AppError(f"Product '{name}' not found", "PRODUCT_NOT_FOUND", 404)
    rows = (
        db.query(Inventory)
        .filter(Inventory.product_id == product.product_id)
        .order_by(Inventory.location_id)
        .all()
    )
    locations = [
        {"location": r.location.location_code, "available_quantity": r.quantity}
        for r in rows
    ]
    total = sum(r.quantity for r in rows)
    can_fulfil = total >= requested_quantity
    return {
        "product": product.name,
        "locations": locations,
        "total_available": total,
        "requested_quantity": requested_quantity,
        "status": "CAN_BE_FULFILLED" if can_fulfil else "INSUFFICIENT_STOCK",
        "shortage": 0 if can_fulfil else requested_quantity - total,
    }
