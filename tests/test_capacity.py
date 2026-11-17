from backend.database import SessionLocal
from backend.models import Inventory, Location, Product
from tests.conftest import dispatch, store


def _snapshot():
    db = SessionLocal()
    try:
        return (
            db.query(Product).count(),
            db.query(Inventory).count(),
            {loc.location_code: loc.occupied_capacity for loc in db.query(Location).all()},
        )
    finally:
        db.close()


def test_store_within_capacity(client):
    r = store(client, "Keyboard", 30)  # exactly fills A2
    assert r.status_code == 201
    assert r.json()["data"]["remaining_capacity"] == 0


def test_batch_larger_than_any_single_shelf_rejected_and_db_unchanged(client):
    before = _snapshot()
    r = store(client, "Server", 101)  # biggest shelf is 100 -> cannot fit in ONE shelf
    assert r.status_code == 409
    assert r.json()["error_code"] == "CAPACITY_EXCEEDED"
    assert _snapshot() == before  # nothing was written, not even the product


def test_full_warehouse_rejects(client):
    # Fill every shelf completely: 50+30+100+100+50+30+30+100+50 = 540
    for i, qty in enumerate([50, 30, 100, 100, 50, 30, 30, 100, 50]):
        r = store(client, f"Filler{i}", qty)
        assert r.status_code == 201, r.json()
    r = store(client, "OneMore", 1)
    assert r.status_code == 409


def test_allocation_moves_to_another_shelf_when_nearest_full(client):
    store(client, "Keyboard", 30)  # fills A2
    r = store(client, "Mouse", 10)
    assert r.status_code == 201
    assert r.json()["data"]["assigned_location"] != "A2"


def test_occupied_capacity_correct_after_dispatch(client):
    store(client, "Keyboard", 10)
    dispatch(client, "Keyboard", 4)
    locations = client.get("/api/v1/warehouse/locations").json()["data"]
    a2 = next(loc for loc in locations if loc["location_code"] == "A2")
    assert a2["occupied_capacity"] == 6
    assert a2["remaining_capacity"] == 24


def test_capacity_endpoint_totals(client):
    store(client, "Keyboard", 10)
    data = client.get("/api/v1/warehouse/capacity").json()["data"]
    assert data["total_capacity"] == 540
    assert data["total_occupied"] == 10
    assert data["total_remaining"] == 530


def test_only_fitting_shelf_unreachable_returns_409(client):
    # Fill every shelf except C2, then block all three pathways into C2.
    for i, qty in enumerate([50, 30, 100, 100, 50, 30, 30, 50]):
        r = store(client, f"Blocker{i}", qty)
        assert r.status_code == 201, r.json()
    edges = client.get("/api/v1/warehouse/map").json()["data"]["edges"]
    for pair in ({"B2", "C2"}, {"C1", "C2"}, {"C2", "C3"}):
        edge = next(e for e in edges if {e["source"], e["destination"]} == pair)
        r = client.patch(f"/api/v1/warehouse/connections/{edge['connection_id']}",
                         json={"is_blocked": True})
        assert r.status_code == 200
    before = _snapshot()
    r = store(client, "Stranded", 50)  # only C2 fits, and it is unreachable
    assert r.status_code == 409
    assert r.json()["error_code"] == "CAPACITY_EXCEEDED"
    assert _snapshot() == before
