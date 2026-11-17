from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.routes.helpers import success
from backend.schemas import DispatchRequest, StoreRequest
from backend.services import inventory_service
from backend.services.allocation_service import store_product
from backend.services.dispatch_service import dispatch_product

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("")
def list_inventory(db: Session = Depends(get_db)):
    return success(inventory_service.list_inventory(db))


@router.get("/locate")
def locate(product_name: str, requested_quantity: int, db: Session = Depends(get_db)):
    return success(inventory_service.locate_product(db, product_name, requested_quantity))


@router.get("/{product_id}")
def inventory_for_product(product_id: int, db: Session = Depends(get_db)):
    return success(inventory_service.inventory_for_product(db, product_id))


@router.post("/store")
def store(payload: StoreRequest, db: Session = Depends(get_db)):
    data = store_product(db, payload.product_name, payload.quantity)
    return success(data, message="Storage successful", status_code=201)


@router.post("/dispatch")
def dispatch(payload: DispatchRequest, db: Session = Depends(get_db)):
    data = dispatch_product(db, payload.product_name, payload.quantity)
    return success(data, message="Dispatch successful")
