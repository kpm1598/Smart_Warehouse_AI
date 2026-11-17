from tests.conftest import dispatch, store


def test_store_new_product(client):
    r = store(client, "Keyboard", 10)
    assert r.status_code == 201
    data = r.json()["data"]
    assert data["product"] == "Keyboard"
    assert data["quantity_stored"] == 10
    assert data["assigned_location"] == "A2"  # nearest eligible shelf
    assert data["algorithm"] == "Greedy Best-First Search"


def test_store_creates_product_record(client):
    store(client, "Webcam", 5)
    products = client.get("/api/v1/products").json()["data"]
    assert [p["name"] for p in products] == ["Webcam"]


def test_restock_same_product_prefers_same_shelf(client):
    store(client, "Keyboard", 10)          # -> A2 (10/30)
    r = store(client, "Keyboard", 5)       # same-product shelf first
    assert r.json()["data"]["assigned_location"] == "A2"
    rows = client.get("/api/v1/inventory").json()["data"]
    assert len(rows) == 1 and rows[0]["quantity"] == 15


def test_same_product_can_live_on_multiple_shelves(client):
    store(client, "Keyboard", 25)          # -> A2 (25/30), remaining 5
    r = store(client, "Keyboard", 20)      # does not fit in A2 -> another shelf
    assert r.json()["data"]["assigned_location"] != "A2"
    rows = client.get("/api/v1/inventory").json()["data"]
    assert len(rows) == 2
    assert sum(row["quantity"] for row in rows) == 45


def test_product_name_case_insensitive(client):
    store(client, "Keyboard", 10)
    r = store(client, "keyboard", 5)
    assert r.status_code == 201
    products = client.get("/api/v1/products").json()["data"]
    assert len(products) == 1
    rows = client.get("/api/v1/inventory").json()["data"]
    assert rows[0]["quantity"] == 15


def test_display_inventory_and_totals(client):
    store(client, "Keyboard", 10)
    store(client, "Mouse", 15)
    summary = client.get("/api/v1/dashboard/summary").json()["data"]
    assert summary["unique_products"] == 2
    assert summary["total_stock_units"] == 25


def test_search_existing_product(client):
    store(client, "Keyboard", 10)
    r = client.get("/api/v1/products/search", params={"name": "key"})
    assert [p["name"] for p in r.json()["data"]] == ["Keyboard"]


def test_search_unknown_product_returns_empty(client):
    r = client.get("/api/v1/products/search", params={"name": "Nope"})
    assert r.json()["data"] == []


def test_locate_known_product_can_be_fulfilled(client):
    store(client, "Keyboard", 10)
    r = client.get("/api/v1/inventory/locate",
                   params={"product_name": "Keyboard", "requested_quantity": 5})
    data = r.json()["data"]
    assert data["status"] == "CAN_BE_FULFILLED"
    assert data["total_available"] == 10
    assert data["locations"][0]["location"] == "A2"


def test_locate_insufficient_stock_reports_shortage(client):
    store(client, "Keyboard", 10)
    r = client.get("/api/v1/inventory/locate",
                   params={"product_name": "Keyboard", "requested_quantity": 15})
    data = r.json()["data"]
    assert data["status"] == "INSUFFICIENT_STOCK"
    assert data["shortage"] == 5


def test_locate_unknown_product_404(client):
    r = client.get("/api/v1/inventory/locate",
                   params={"product_name": "Ghost", "requested_quantity": 1})
    assert r.status_code == 404
    assert r.json()["error_code"] == "PRODUCT_NOT_FOUND"


def test_store_rejects_empty_name_and_bad_quantity(client):
    r = client.post("/api/v1/inventory/store", json={"product_name": "  ", "quantity": 5})
    assert r.status_code == 422
    r = client.post("/api/v1/inventory/store", json={"product_name": "X", "quantity": 0})
    assert r.status_code == 422
    r = client.post("/api/v1/inventory/store", json={"product_name": "X", "quantity": -3})
    assert r.status_code == 422


def test_inventory_for_product_endpoint(client):
    store(client, "Keyboard", 10)
    pid = client.get("/api/v1/products").json()["data"][0]["product_id"]
    data = client.get(f"/api/v1/inventory/{pid}").json()["data"]
    assert data["total_quantity"] == 10
    r = client.get("/api/v1/inventory/99999")
    assert r.status_code == 404
