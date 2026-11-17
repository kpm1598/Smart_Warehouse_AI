from backend.algorithms.greedy import greedy_search
from backend.database import SessionLocal
from backend.graph import build_graph


def _graph(client):
    db = SessionLocal()
    try:
        return build_graph(db)
    finally:
        db.close()


def _manual_graph():
    # S(0,0); X(0,2) far from goal; Y(1,0) close to goal; G(2,0)
    nodes = {c: {"row": r, "column": col} for c, r, col in
             [("S", 0, 0), ("X", 0, 2), ("Y", 1, 0), ("G", 2, 0)]}
    adjacency = {
        "S": [("X", 3.0), ("Y", 1.0)],
        "X": [("S", 3.0), ("G", 1.0)],
        "Y": [("S", 1.0), ("G", 1.0)],
        "G": [("X", 1.0), ("Y", 1.0)],
    }
    return {"nodes": nodes, "adjacency": adjacency}


def test_heuristic_ordering_prefers_lower_h_first():
    result = greedy_search(_manual_graph(), "S", goal="G")
    assert result["status"] == "SUCCESS"
    # Y (h=1) is explored before X (h=4) even though X was listed first.
    assert result["nodes_explored"] == ["S", "Y", "G"]


def test_path_reconstruction_and_distance():
    result = greedy_search(_manual_graph(), "S", goal="G")
    assert result["path"] == ["S", "Y", "G"]
    assert result["path_distance"] == 2.0
    assert result["nodes_explored_count"] == len(result["nodes_explored"])
    assert result["execution_time_ms"] >= 0


def test_allocation_mode_finds_nearby_eligible():
    graph = _manual_graph()
    result = greedy_search(graph, "S", eligible={"X", "Y"})
    assert result["status"] == "SUCCESS"
    assert result["selected_location"] == "Y"  # nearest eligible to S


def test_allocation_failure_when_no_eligible():
    result = greedy_search(_manual_graph(), "S", eligible=set())
    assert result["status"] == "FAILURE"
    assert result["selected_location"] is None


def test_greedy_skips_locations_without_capacity_via_api(client):
    # A2 (cap 30) cannot fit 40; allocation must choose a bigger shelf.
    r = client.post("/api/v1/ai/search/greedy",
                    json={"start_location": "RECEIVING", "quantity_required": 40})
    data = r.json()["data"]
    assert data["status"] == "SUCCESS"
    assert data["selected_location"] != "A2"
    assert data["selected_location"] != "RECEIVING"


def test_greedy_avoids_blocked_a2_b2_pathway(client):
    # A2<->B2 is blocked in the seed; the path to B2 must go around it.
    r = client.post("/api/v1/ai/search/greedy",
                    json={"start_location": "RECEIVING", "goal_location": "B2"})
    data = r.json()["data"]
    assert data["status"] == "SUCCESS"
    assert data["path"][-1] == "B2"
    pairs = list(zip(data["path"], data["path"][1:]))
    assert ("A2", "B2") not in pairs and ("B2", "A2") not in pairs


def test_greedy_on_real_graph_reaches_all_shelves(client):
    graph = _graph(client)
    for code in ["A1", "A3", "B1", "B3", "C1", "C2", "C3"]:
        result = greedy_search(graph, "RECEIVING", goal=code)
        assert result["status"] == "SUCCESS", code
        assert result["path"][0] == "RECEIVING" and result["path"][-1] == code
