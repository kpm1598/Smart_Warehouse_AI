"""HTTP client for the terminal interface.

Talks ONLY to the shared FastAPI backend — the terminal keeps no data of
its own, so anything stored here is immediately visible on the webpage
(and vice versa).
"""
import os

import requests

BASE_URL = os.environ.get("WAREHOUSE_API_BASE", "http://127.0.0.1:8000/api/v1")
TIMEOUT = 5


class ApiUnavailable(Exception):
    pass


class ApiError(Exception):
    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def _request(method, path, **kwargs):
    try:
        response = requests.request(
            method, f"{BASE_URL}{path}", timeout=TIMEOUT, **kwargs
        )
    except requests.RequestException:
        raise ApiUnavailable(
            "Cannot reach the warehouse server. "
            "Start the backend first (run_backend.bat), then try again."
        )
    try:
        body = response.json()
    except ValueError:
        raise ApiError("The server returned an invalid response.", response.status_code)
    if not body.get("success", False):
        raise ApiError(body.get("message", "Request failed"), response.status_code)
    return body.get("data")


def store_product(product_name, quantity):
    return _request("POST", "/inventory/store",
                    json={"product_name": product_name, "quantity": quantity})


def list_inventory():
    return _request("GET", "/inventory")


def locate_product(product_name, requested_quantity):
    return _request(
        "GET", "/inventory/locate",
        params={"product_name": product_name, "requested_quantity": requested_quantity},
    )


def dispatch_product(product_name, quantity):
    return _request("POST", "/inventory/dispatch",
                    json={"product_name": product_name, "quantity": quantity})


def list_locations():
    return _request("GET", "/warehouse/locations")


def dashboard_summary():
    return _request("GET", "/dashboard/summary")


def compare_search(start_location, goal_location, depth_limit):
    return _request(
        "POST", "/ai/search/compare",
        json={
            "start_location": start_location,
            "goal_location": goal_location,
            "depth_limit": depth_limit,
        },
    )
