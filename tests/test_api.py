from tests.conftest import store


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "ok"


def test_success_wrapper_shape(client):
    r = client.get("/api/v1/products")
    body = r.json()
    assert body["success"] is True
    assert "message" in body and "data" in body


def test_error_wrapper_shape(client):
    r = client.get("/api/v1/products/424242")
    assert r.status_code == 404
    body = r.json()
    assert body["success"] is False
    assert body["error_code"] == "PRODUCT_NOT_FOUND"


def test_validation_error_is_422_with_wrapper(client):
    r = client.post("/api/v1/products", json={"name": "   "})
    assert r.status_code == 422
    assert r.json()["error_code"] == "VALIDATION_ERROR"


def test_create_product_201_and_duplicate_409(client):
    r = client.post("/api/v1/products", json={"name": "Keyboard"})
    assert r.status_code == 201
    r = client.post("/api/v1/products", json={"name": "KEYBOARD"})
    assert r.status_code == 409


def test_dashboard_summary_and_recent_activity(client):
    store(client, "Keyboard", 10)
    summary = client.get("/api/v1/dashboard/summary").json()["data"]
    assert summary["unique_products"] == 1
    assert summary["total_locations"] == 10
    assert summary["storage_locations"] == 9
    activity = client.get("/api/v1/dashboard/recent-activity").json()["data"]
    assert activity[0]["product"] == "Keyboard"
    assert activity[0]["movement_type"] == "IN"


def test_warehouse_locations_and_detail(client):
    locations = client.get("/api/v1/warehouse/locations").json()["data"]
    assert len(locations) == 10
    codes = {loc["location_code"] for loc in locations}
    assert codes == {"RECEIVING", "A1", "A2", "A3", "B1", "B2", "B3", "C1", "C2", "C3"}
    detail = client.get("/api/v1/warehouse/locations/A2").json()["data"]
    assert detail["max_capacity"] == 30
    assert client.get("/api/v1/warehouse/locations/ZZ").status_code == 404


def test_warehouse_map_seed_blocked_pathway(client):
    data = client.get("/api/v1/warehouse/map").json()["data"]
    assert len(data["nodes"]) == 10
    blocked = [e for e in data["edges"] if e["is_blocked"]]
    assert len(blocked) == 1
    assert {blocked[0]["source"], blocked[0]["destination"]} == {"A2", "B2"}


def test_patch_connection_updates_both_directions(client):
    edges = client.get("/api/v1/warehouse/map").json()["data"]["edges"]
    edge = next(e for e in edges if {e["source"], e["destination"]} == {"A1", "B1"})
    r = client.patch(f"/api/v1/warehouse/connections/{edge['connection_id']}",
                     json={"is_blocked": True})
    assert r.status_code == 200
    assert r.json()["data"]["updated_rows"] == 2
    a1 = client.get("/api/v1/warehouse/locations/A1").json()["data"]
    b1 = client.get("/api/v1/warehouse/locations/B1").json()["data"]
    assert next(c for c in a1["connections"] if c["to"] == "B1")["is_blocked"] is True
    assert next(c for c in b1["connections"] if c["to"] == "A1")["is_blocked"] is True
    r = client.patch("/api/v1/warehouse/connections/99999", json={"is_blocked": True})
    assert r.status_code == 404


def test_compare_returns_real_measured_metrics(client):
    r = client.post("/api/v1/ai/search/compare",
                    json={"start_location": "RECEIVING", "goal_location": "C3",
                          "depth_limit": 4})
    data = r.json()["data"]
    for key in ("greedy", "dls"):
        metrics = data[key]
        assert metrics["route_found"] is True
        assert metrics["nodes_explored"] > 0
        assert metrics["path_distance"] == 4.0
        assert metrics["execution_time_ms"] >= 0
        assert metrics["path"][-1] == "C3"
    assert data["greedy"]["search_type"] == "Informed"
    assert data["greedy"]["heuristic_used"] is True
    assert data["dls"]["search_type"] == "Uninformed"
    assert data["dls"]["heuristic_used"] is False
    assert data["dls"]["depth_limit"] == 4


def test_frontend_pages_served(client):
    for page in ["/", "/inventory.html", "/store.html", "/locate.html",
                 "/dispatch.html", "/warehouse.html", "/comparison.html"]:
        r = client.get(page)
        assert r.status_code == 200, page
        assert "Smart Warehouse AI" in r.text
