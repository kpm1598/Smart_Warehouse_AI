from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Inventory, Location, Product, StockMovement
from backend.routes.helpers import success

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    locations = db.query(Location).all()
    storage = [loc for loc in locations if loc.max_capacity > 0]
    data = {
        "unique_products": db.query(Product).count(),
        "total_stock_units": sum(r.quantity for r in db.query(Inventory).all()),
        "total_locations": len(locations),
        "storage_locations": len(storage),
        "occupied_locations": len({r.location_id for r in db.query(Inventory).all()}),
        "available_locations": len([loc for loc in storage if loc.remaining_capacity > 0]),
        "total_capacity": sum(loc.max_capacity for loc in storage),
        "total_occupied_capacity": sum(loc.occupied_capacity for loc in storage),
        "total_remaining_capacity": sum(loc.remaining_capacity for loc in storage),
        "recent_activity": _recent(db, 5),
    }
    return success(data)


def _recent(db, limit):
    rows = (
        db.query(StockMovement)
        .order_by(StockMovement.movement_id.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "movement_id": r.movement_id,
            "product": r.product.name,
            "location": r.location.location_code,
            "movement_type": r.movement_type,
            "quantity": r.quantity,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in rows
    ]


@router.get("/recent-activity")
def recent_activity(limit: int = 10, db: Session = Depends(get_db)):
    return success(_recent(db, max(1, min(limit, 100))))
