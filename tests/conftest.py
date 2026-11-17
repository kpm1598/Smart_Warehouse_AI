"""Test fixtures.

A temporary database is used (WAREHOUSE_DB_PATH is set BEFORE the app is
imported) so tests NEVER touch the real demo database in data/.
State is reset before every test: inventory/products/movements cleared,
occupied capacities zeroed, and connections restored to the seed default
(only A2<->B2 blocked).
"""
import os
import tempfile

_TMP = tempfile.mkdtemp(prefix="sw-tests-")
os.environ["WAREHOUSE_DB_PATH"] = os.path.join(_TMP, "test_warehouse.db")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from backend.database import SessionLocal, init_db  # noqa: E402
from backend.main import app  # noqa: E402
from backend.models import (  # noqa: E402
    Inventory,
    Location,
    Product,
    StockMovement,
    WarehouseConnection,
)


@pytest.fixture(scope="session")
def client():
    init_db()
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(autouse=True)
def reset_state(client):
    db = SessionLocal()
    try:
        db.query(StockMovement).delete()
        db.query(Inventory).delete()
        db.query(Product).delete()
        for loc in db.query(Location).all():
            loc.occupied_capacity = 0
        by_code = {loc.location_code: loc.location_id for loc in db.query(Location).all()}
        for conn in db.query(WarehouseConnection).all():
            src = next(c for c, i in by_code.items() if i == conn.source_location_id)
            dst = next(c for c, i in by_code.items() if i == conn.destination_location_id)
            conn.is_blocked = {src, dst} == {"A2", "B2"}
        db.commit()
    finally:
        db.close()
    yield


def store(client, name, quantity):
    return client.post("/api/v1/inventory/store",
                       json={"product_name": name, "quantity": quantity})


def dispatch(client, name, quantity):
    return client.post("/api/v1/inventory/dispatch",
                       json={"product_name": name, "quantity": quantity})
