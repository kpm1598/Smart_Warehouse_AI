from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.routes.helpers import success
from backend.schemas import ConnectionPatch
from backend.services import warehouse_service

router = APIRouter(prefix="/warehouse", tags=["warehouse"])


@router.get("/locations")
def locations(db: Session = Depends(get_db)):
    return success(warehouse_service.list_locations(db))


@router.get("/locations/{location_code}")
def location_detail(location_code: str, db: Session = Depends(get_db)):
    return success(warehouse_service.get_location(db, location_code))


@router.get("/map")
def warehouse_map(db: Session = Depends(get_db)):
    return success(warehouse_service.warehouse_map(db))


@router.get("/capacity")
def capacity(db: Session = Depends(get_db)):
    return success(warehouse_service.capacity_summary(db))


@router.patch("/connections/{connection_id}")
def patch_connection(connection_id: int, payload: ConnectionPatch, db: Session = Depends(get_db)):
    data = warehouse_service.set_connection_blocked(db, connection_id, payload.is_blocked)
    return success(data, message="Connection updated")
