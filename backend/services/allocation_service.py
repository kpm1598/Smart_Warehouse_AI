"""Stock-in: Greedy Best-First Search allocation + transactional update.

Rules (approved decisions):
  * A batch must fit COMPLETELY into one single shelf — no splitting,
    no partial store; on failure the database is left unchanged.
  * The same product may live on several shelves from separate batches.
  * Same-product shelves are tried first (Greedy over that eligible subset);
    if none fits, Greedy runs over all eligible shelves.
  * The AI engine only *recommends* a location; this service re-validates
    capacity inside the transaction before writing anything.
"""
from sqlalchemy import func

from backend.algorithms.greedy import greedy_search
from backend.config import START_LOCATION
from backend.graph import build_graph
from backend.models import Inventory, Location, Product, StockMovement
from backend.services.errors import AppError


def get_product_by_name(db, name):
    return (
        db.query(Product)
        .filter(func.lower(Product.name) == name.strip().lower())
        .first()
    )


def store_product(db, product_name, quantity):
    name = (product_name or "").strip()
    if not name:
        raise AppError("Product name must not be empty", "VALIDATION_ERROR", 422)
    if quantity is None or quantity <= 0:
        raise AppError("Quantity must be greater than zero", "VALIDATION_ERROR", 422)

    try:
        product = get_product_by_name(db, name)
        if product is None:
            product = Product(name=name)
            db.add(product)
            db.flush()

        locations = db.query(Location).all()
        eligible = {
            loc.location_code
            for loc in locations
            if loc.is_active
            and loc.location_code != START_LOCATION
            and loc.max_capacity > 0
            and loc.remaining_capacity >= quantity
        }
        if not eligible:
            raise AppError(
                "No single shelf has enough remaining capacity for this batch",
                "CAPACITY_EXCEEDED",
                409,
            )

        existing_codes = {
            row.location.location_code
            for row in db.query(Inventory).filter(Inventory.product_id == product.product_id).all()
        }
        same_product_eligible = eligible & existing_codes

        graph = build_graph(db)
        result = None
        if same_product_eligible:
            result = greedy_search(graph, START_LOCATION, eligible=same_product_eligible)
        if result is None or result["status"] != "SUCCESS":
            result = greedy_search(graph, START_LOCATION, eligible=eligible)
        if result["status"] != "SUCCESS":
            raise AppError(
                "No reachable shelf can store this batch (paths may be blocked)",
                "CAPACITY_EXCEEDED",
                409,
            )

        chosen_code = result["selected_location"]
        location = next(loc for loc in locations if loc.location_code == chosen_code)
        # Re-validate inside the transaction before mutating anything.
        if location.remaining_capacity < quantity:
            raise AppError(
                "Selected shelf no longer has enough capacity",
                "CAPACITY_EXCEEDED",
                409,
            )

        row = (
            db.query(Inventory)
            .filter(
                Inventory.product_id == product.product_id,
                Inventory.location_id == location.location_id,
            )
            .first()
        )
        if row is None:
            row = Inventory(
                product_id=product.product_id,
                location_id=location.location_id,
                quantity=quantity,
            )
            db.add(row)
        else:
            row.quantity += quantity
        location.occupied_capacity += quantity
        db.add(
            StockMovement(
                product_id=product.product_id,
                location_id=location.location_id,
                movement_type="IN",
                quantity=quantity,
            )
        )
        db.commit()
        db.refresh(location)
        return {
            "product": product.name,
            "quantity_stored": quantity,
            "assigned_location": chosen_code,
            "remaining_capacity": location.remaining_capacity,
            "algorithm": "Greedy Best-First Search",
            "path": result["path"],
            "nodes_explored": result["nodes_explored"],
            "nodes_explored_count": result["nodes_explored_count"],
            "path_distance": result["path_distance"],
        }
    except AppError:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        raise
