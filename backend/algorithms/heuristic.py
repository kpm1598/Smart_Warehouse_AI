"""Heuristic function for Greedy Best-First Search."""


def manhattan_distance(row_a, col_a, row_b, col_b):
    """Manhattan distance between two grid coordinates."""
    return abs(row_a - row_b) + abs(col_a - col_b)
