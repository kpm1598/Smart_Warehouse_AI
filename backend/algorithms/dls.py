"""Depth-Limited Search — implemented manually (textbook recursive DLS).

Result semantics (TDD section 7.3):
  SUCCESS — goal found within the depth limit.
  CUTOFF  — at least one branch hit the depth limit without finding the goal
            (this does NOT prove the goal is unreachable).
  FAILURE — the reachable space within the limit was exhausted with no cutoff.

Cycle avoidance uses current-path membership only (no global visited set),
so a node can still be reached later via a different path.
Blocked edges are absent from the graph snapshot, so they are never traversed.
"""
import time


def depth_limited_search(graph, start, goal, depth_limit):
    nodes = graph["nodes"]
    adjacency = graph["adjacency"]
    explored = []
    state = {"depth_reached": 0, "cutoff_seen": False}

    started = time.perf_counter()

    def recursive_dls(node, depth_remaining, path):
        explored.append(node)
        depth_used = depth_limit - depth_remaining
        if depth_used > state["depth_reached"]:
            state["depth_reached"] = depth_used
        if node == goal:
            return list(path)
        if depth_remaining == 0:
            state["cutoff_seen"] = True
            return None
        for neighbour, _distance in adjacency.get(node, []):
            if neighbour in path:  # cycle avoidance: current path only
                continue
            result = recursive_dls(neighbour, depth_remaining - 1, path + [neighbour])
            if result is not None:
                return result
        return None

    if start not in nodes or goal not in nodes:
        return {"status": "FAILURE", "path": [], "nodes_explored": [],
                "nodes_explored_count": 0, "depth_reached": 0,
                "path_distance": 0.0, "execution_time_ms": 0.0}

    found_path = recursive_dls(start, depth_limit, [start])
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    if found_path is not None:
        distance = 0.0
        for a, b in zip(found_path, found_path[1:]):
            for neighbour, dist in adjacency.get(a, []):
                if neighbour == b:
                    distance += dist
                    break
        return {"status": "SUCCESS", "path": found_path,
                "nodes_explored": explored, "nodes_explored_count": len(explored),
                "depth_reached": state["depth_reached"],
                "path_distance": distance,
                "execution_time_ms": round(elapsed_ms, 4)}

    status = "CUTOFF" if state["cutoff_seen"] else "FAILURE"
    return {"status": status, "path": [],
            "nodes_explored": explored, "nodes_explored_count": len(explored),
            "depth_reached": state["depth_reached"],
            "path_distance": 0.0,
            "execution_time_ms": round(elapsed_ms, 4)}
