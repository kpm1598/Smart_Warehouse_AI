"""Greedy Best-First Search — implemented manually (no external library).

One core loop serves two modes:
  * navigation mode: single goal location, h(n) = Manhattan distance to goal.
  * allocation mode: goal test = node is in the eligible-location set,
    h(n) = Manhattan distance to the NEAREST eligible location.

The algorithm only reads the graph snapshot it is given; it never touches
the database and never mutates inventory.
"""
import heapq
import time

from backend.algorithms.heuristic import manhattan_distance


def _reconstruct_path(parent, start, goal):
    path = [goal]
    while path[-1] != start:
        path.append(parent[path[-1]])
    path.reverse()
    return path


def _path_distance(path, adjacency):
    total = 0.0
    for a, b in zip(path, path[1:]):
        for neighbour, distance in adjacency.get(a, []):
            if neighbour == b:
                total += distance
                break
    return total


def greedy_search(graph, start, goal=None, eligible=None):
    """Run Greedy Best-First Search on a graph snapshot.

    graph: {"nodes": {code: {"row":..,"column":..}}, "adjacency": {code: [(code, dist)]}}
    Provide exactly one of `goal` (navigation) or `eligible` (allocation, a set of codes).
    """
    nodes = graph["nodes"]
    adjacency = graph["adjacency"]
    if start not in nodes:
        return {"status": "FAILURE", "path": [], "selected_location": None,
                "nodes_explored": [], "nodes_explored_count": 0,
                "path_distance": 0.0, "execution_time_ms": 0.0}

    if goal is not None:
        target = nodes[goal]

        def heuristic(code):
            info = nodes[code]
            return manhattan_distance(info["row"], info["column"], target["row"], target["column"])

        def is_goal(code):
            return code == goal

    else:
        eligible = eligible or set()

        def heuristic(code):
            info = nodes[code]
            if not eligible:
                return 0
            return min(
                manhattan_distance(info["row"], info["column"],
                                   nodes[e]["row"], nodes[e]["column"])
                for e in eligible
            )

        def is_goal(code):
            return code in eligible

    started = time.perf_counter()
    # Priority is the heuristic h(n) — that is what makes this Greedy.
    # Ties are broken by the real distance travelled so far, then by code,
    # which keeps the choice deterministic and prefers the shorter real
    # route among equally promising nodes.
    open_heap = [(heuristic(start), 0.0, start)]
    explored = []
    explored_set = set()
    parent = {start: None}
    distance_from_start = {start: 0.0}
    in_open = {start}
    found = None

    while open_heap:
        _, current_distance, current = heapq.heappop(open_heap)
        in_open.discard(current)
        if current in explored_set:
            continue
        explored_set.add(current)
        explored.append(current)
        if is_goal(current):
            found = current
            break
        for neighbour, edge_distance in adjacency.get(current, []):
            if neighbour in explored_set or neighbour in in_open:
                continue
            parent[neighbour] = current
            distance_from_start[neighbour] = current_distance + edge_distance
            in_open.add(neighbour)
            heapq.heappush(
                open_heap,
                (heuristic(neighbour), distance_from_start[neighbour], neighbour),
            )

    elapsed_ms = (time.perf_counter() - started) * 1000.0
    if found is None:
        return {"status": "FAILURE", "path": [], "selected_location": None,
                "nodes_explored": explored, "nodes_explored_count": len(explored),
                "path_distance": 0.0, "execution_time_ms": round(elapsed_ms, 4)}

    path = _reconstruct_path(parent, start, found)
    return {
        "status": "SUCCESS",
        "path": path,
        "selected_location": found,
        "goal_location": found,
        "nodes_explored": explored,
        "nodes_explored_count": len(explored),
        "path_distance": _path_distance(path, adjacency),
        "heuristic_at_start": heuristic(start),
        "execution_time_ms": round(elapsed_ms, 4),
    }
