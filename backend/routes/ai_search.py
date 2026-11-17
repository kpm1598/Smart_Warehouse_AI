"""AI search endpoints: Greedy, DLS, and the side-by-side comparison.

Both algorithms solve the SAME single-goal navigation problem in the
comparison endpoint (approved decision), so the metrics are comparable.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.algorithms.dls import depth_limited_search
from backend.algorithms.greedy import greedy_search
from backend.database import get_db
from backend.graph import build_graph
from backend.models import Location
from backend.routes.helpers import success
from backend.schemas import CompareRequest, DLSSearchRequest, GreedySearchRequest
from backend.services.errors import AppError

router = APIRouter(prefix="/ai/search", tags=["ai-search"])


def _validate_locations(db, *codes):
    known = {loc.location_code for loc in db.query(Location).all()}
    for code in codes:
        if code is not None and code not in known:
            raise AppError(f"Location '{code}' not found", "LOCATION_NOT_FOUND", 404)


@router.post("/greedy")
def greedy(payload: GreedySearchRequest, db: Session = Depends(get_db)):
    _validate_locations(db, payload.start_location, payload.goal_location)
    graph = build_graph(db)
    if payload.goal_location:
        result = greedy_search(graph, payload.start_location, goal=payload.goal_location)
        result["mode"] = "navigation"
    elif payload.quantity_required is not None:
        locations = db.query(Location).all()
        eligible = {
            loc.location_code
            for loc in locations
            if loc.is_active and loc.max_capacity > 0
            and loc.location_code != payload.start_location
            and loc.remaining_capacity >= payload.quantity_required
        }
        result = greedy_search(graph, payload.start_location, eligible=eligible)
        result["mode"] = "allocation"
        result["quantity_required"] = payload.quantity_required
    else:
        raise AppError(
            "Provide goal_location (navigation) or quantity_required (allocation)",
            "VALIDATION_ERROR",
            422,
        )
    result["algorithm"] = "Greedy Best-First Search"
    result["start_location"] = payload.start_location
    return success(result)


@router.post("/dls")
def dls(payload: DLSSearchRequest, db: Session = Depends(get_db)):
    _validate_locations(db, payload.start_location, payload.goal_location)
    graph = build_graph(db)
    result = depth_limited_search(
        graph, payload.start_location, payload.goal_location, payload.depth_limit
    )
    result["algorithm"] = "Depth-Limited Search"
    result["start_location"] = payload.start_location
    result["goal_location"] = payload.goal_location
    result["depth_limit"] = payload.depth_limit
    return success(result)


@router.post("/compare")
def compare(payload: CompareRequest, db: Session = Depends(get_db)):
    _validate_locations(db, payload.start_location, payload.goal_location)
    graph = build_graph(db)
    greedy_result = greedy_search(graph, payload.start_location, goal=payload.goal_location)
    dls_result = depth_limited_search(
        graph, payload.start_location, payload.goal_location, payload.depth_limit
    )
    data = {
        "start_location": payload.start_location,
        "goal_location": payload.goal_location,
        "depth_limit": payload.depth_limit,
        "greedy": {
            "algorithm": "Greedy Best-First Search",
            "search_type": "Informed",
            "heuristic_used": True,
            "depth_limit": None,
            "status": greedy_result["status"],
            "route_found": greedy_result["status"] == "SUCCESS",
            "path": greedy_result["path"],
            "nodes_explored": greedy_result["nodes_explored_count"],
            "nodes_explored_order": greedy_result["nodes_explored"],
            "path_distance": greedy_result["path_distance"],
            "execution_time_ms": greedy_result["execution_time_ms"],
        },
        "dls": {
            "algorithm": "Depth-Limited Search",
            "search_type": "Uninformed",
            "heuristic_used": False,
            "depth_limit": payload.depth_limit,
            "status": dls_result["status"],
            "route_found": dls_result["status"] == "SUCCESS",
            "path": dls_result["path"],
            "nodes_explored": dls_result["nodes_explored_count"],
            "nodes_explored_order": dls_result["nodes_explored"],
            "path_distance": dls_result["path_distance"],
            "execution_time_ms": dls_result["execution_time_ms"],
        },
    }
    return success(data)
