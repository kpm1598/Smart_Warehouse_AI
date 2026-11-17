from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Product
from backend.routes.helpers import failure, success
from backend.schemas import ProductCreate

router = APIRouter(prefix="/products", tags=["products"])


def _to_dict(product):
    return {
        "product_id": product.product_id,
        "name": product.name,
        "created_at": product.created_at.isoformat() if product.created_at else None,
    }


# NOTE: /search must be registered before /{product_id} so it is not
# swallowed by the path parameter.
@router.get("/search")
def search_products(name: str = "", db: Session = Depends(get_db)):
    query = db.query(Product)
    if name.strip():
        query = query.filter(func.lower(Product.name).contains(name.strip().lower()))
    return success([_to_dict(p) for p in query.order_by(Product.name).all()])


@router.get("")
def list_products(db: Session = Depends(get_db)):
    products = db.query(Product).order_by(Product.name).all()
    return success([_to_dict(p) for p in products])


@router.get("/{product_id}")
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.query(Product).filter(Product.product_id == product_id).first()
    if product is None:
        return failure("Product not found", "PRODUCT_NOT_FOUND", 404)
    return success(_to_dict(product))


@router.post("")
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(Product)
        .filter(func.lower(Product.name) == payload.name.lower())
        .first()
    )
    if existing is not None:
        return failure("Product already exists", "PRODUCT_EXISTS", 409)
    product = Product(name=payload.name)
    db.add(product)
    db.commit()
    db.refresh(product)
    return success(_to_dict(product), message="Product created", status_code=201)
