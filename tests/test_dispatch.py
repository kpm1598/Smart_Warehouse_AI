from backend.database import SessionLocal
from backend.models import Inventory, StockMovement
from tests.conftest import dispatch, store


def _movement_count(mtype=None):
    db = SessionLocal()
    try:
        q = db.query(StockMovement)
        if mtype:
            q = q.filter(StockMovement.movement_type == mtype)
        return q.count()
    finally:
        db.close()


def test_dispatch_valid_quantity(client):
    store(client, "Keyboard", 10)
    r = dispatch(client, "Keyboard", 4)
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["quantity_dispatched"] == 4
    assert data["remaining_stock"] == 6


def test_dispatch_entire_quantity_removes_inventory_row(client):
    store(client, "Keyboard", 10)
    dispatch(client, "Keyboard", 10)
    assert client.get("/api/v1/inventory").json()["data"] == []
    # ...but movement history is preserved (IN + OUT)
    assert _movement_count() == 2
    assert _movement_count("OUT") == 1


def test_dispatch_more_than_available_is_atomic(client):
    store(client, "Keyboard", 10)
    r = dispatch(client, "Keyboard", 15)
    assert r.status_code == 409
    assert r.json()["error_code"] == "INSUFFICIENT_STOCK"
    rows = client.get("/api/v1/inventory").json()["data"]
    assert rows[0]["quantity"] == 10  # unchanged
    assert _movement_count("OUT") == 0


def test_dispatch_unknown_product_404(client):
    r = dispatch(client, "Ghost", 1)
    assert r.status_code == 404


def test_dispatch_from_multiple_locations_deterministic_order(client):
    store(client, "Keyboard", 25)   # A2 (dist 1 from RECEIVING)
    store(client, "Keyboard", 20)   # another shelf (farther away)
    r = dispatch(client, "Keyboard", 30)
    data = r.json()["data"]
    # Nearest shelf (A2) is drained first, then 5 from the next shelf.
    assert data["locations_affected"][0]["location"] == "A2"
    assert data["locations_affected"][0]["quantity_dispatched"] == 25
    assert data["locations_affected"][1]["quantity_dispatched"] == 5
    assert data["remaining_stock"] == 15
    rows = client.get("/api/v1/inventory").json()["data"]
    assert len(rows) == 1 and rows[0]["quantity"] == 15
