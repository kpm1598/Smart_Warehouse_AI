from backend.algorithms.dls import depth_limited_search


def _line_graph():
    # A - B - C - D line, plus isolated Z
    nodes = {c: {"row": 0, "column": i} for i, c in enumerate(["A", "B", "C", "D"])}
    nodes["Z"] = {"row": 9, "column": 9}
    adjacency = {
        "A": [("B", 1.0)],
        "B": [("A", 1.0), ("C", 1.0)],
        "C": [("B", 1.0), ("D", 1.0)],
        "D": [("C", 1.0)],
        "Z": [],
    }
    return {"nodes": nodes, "adjacency": adjacency}


def test_dls_finds_goal_within_limit():
    result = depth_limited_search(_line_graph(), "A", "D", 3)
    assert result["status"] == "SUCCESS"
    assert result["path"] == ["A", "B", "C", "D"]
    assert result["path_distance"] == 3.0


def test_dls_cutoff_when_goal_beyond_limit():
    result = depth_limited_search(_line_graph(), "A", "D", 2)
    assert result["status"] == "CUTOFF"  # NOT failure: goal may exist deeper
    assert result["path"] == []
    assert result["depth_reached"] == 2


def test_dls_failure_when_no_route_exists():
    result = depth_limited_search(_line_graph(), "A", "Z", 10)
    assert result["status"] == "FAILURE"
    assert result["path"] == []


def test_dls_avoids_cycles():
    # Triangle A-B-C-A with goal C: must terminate and return a simple path.
    nodes = {c: {"row": 0, "column": i} for i, c in enumerate(["A", "B", "C"])}
    adjacency = {
        "A": [("B", 1.0), ("C", 1.0)],
        "B": [("A", 1.0), ("C", 1.0)],
        "C": [("A", 1.0), ("B", 1.0)],
    }
    graph = {"nodes": nodes, "adjacency": adjacency}
    result = depth_limited_search(graph, "A", "C", 5)
    assert result["status"] == "SUCCESS"
    assert len(result["path"]) == len(set(result["path"]))  # no repeated nodes


def test_dls_respects_blocked_pathway_via_api(client):
    # Seeded block A2<->B2: any successful DLS route to B2 avoids that edge.
    r = client.post("/api/v1/ai/search/dls",
                    json={"start_location": "RECEIVING", "goal_location": "B2",
                          "depth_limit": 6})
    data = r.json()["data"]
    assert data["status"] == "SUCCESS"
    pairs = list(zip(data["path"], data["path"][1:]))
    assert ("A2", "B2") not in pairs and ("B2", "A2") not in pairs


def test_dls_api_cutoff_and_success(client):
    r = client.post("/api/v1/ai/search/dls",
                    json={"start_location": "RECEIVING", "goal_location": "C1",
                          "depth_limit": 1})
    assert r.json()["data"]["status"] == "CUTOFF"
    r = client.post("/api/v1/ai/search/dls",
                    json={"start_location": "RECEIVING", "goal_location": "C1",
                          "depth_limit": 10})
    data = r.json()["data"]
    assert data["status"] == "SUCCESS"
    assert data["path"][0] == "RECEIVING" and data["path"][-1] == "C1"
    assert len(data["path"]) - 1 <= 10


def test_dls_unknown_location_404(client):
    r = client.post("/api/v1/ai/search/dls",
                    json={"start_location": "RECEIVING", "goal_location": "ZZ",
                          "depth_limit": 3})
    assert r.status_code == 404
