"""Terminal <-> web synchronisation.

Part 1 uses two independent TestClient instances (two "clients", one app,
one database). Part 2 runs the REAL terminal api_client (requests) against
a REAL uvicorn subprocess on its own scratch database, then checks the
result through plain HTTP — exactly how the webpage would see it.
"""
import importlib
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from fastapi.testclient import TestClient

from backend.database import SessionLocal
from backend.main import app
from backend.models import Inventory, Location
from tests.conftest import dispatch, store

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PORT = 8765
BASE = f"http://127.0.0.1:{PORT}"


def assert_capacity_invariant():
    db = SessionLocal()
    try:
        sums = {}
        for row in db.query(Inventory).all():
            sums[row.location_id] = sums.get(row.location_id, 0) + row.quantity
        for loc in db.query(Location).all():
            assert loc.occupied_capacity == sums.get(loc.location_id, 0), loc.location_code
            assert 0 <= loc.occupied_capacity <= loc.max_capacity
    finally:
        db.close()


def test_two_clients_share_one_database(client):
    with TestClient(app) as client_a, TestClient(app) as client_b:
        # "Terminal" stores; "webpage" must see it immediately.
        r = store(client_a, "Keyboard", 10)
        assert r.status_code == 201
        rows_b = client_b.get("/api/v1/inventory").json()["data"]
        assert len(rows_b) == 1 and rows_b[0]["quantity"] == 10
        # "Webpage" dispatches; "terminal" must see the reduced stock.
        r = dispatch(client_b, "Keyboard", 4)
        assert r.status_code == 200
        located = client_a.get(
            "/api/v1/inventory/locate",
            params={"product_name": "Keyboard", "requested_quantity": 6},
        ).json()["data"]
        assert located["total_available"] == 6
        assert located["status"] == "CAN_BE_FULFILLED"
    assert_capacity_invariant()


def test_terminal_api_client_against_live_uvicorn(tmp_path, monkeypatch):
    env = dict(os.environ)
    env["WAREHOUSE_DB_PATH"] = str(tmp_path / "live.db")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app",
         "--host", "127.0.0.1", "--port", str(PORT)],
        cwd=str(PROJECT_ROOT), env=env,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    try:
        deadline = time.time() + 30
        while True:
            try:
                if requests.get(f"{BASE}/health", timeout=2).status_code == 200:
                    break
            except requests.RequestException:
                pass
            if time.time() > deadline:
                raise AssertionError("uvicorn test server did not start in 30s")
            time.sleep(0.3)

        monkeypatch.setenv("WAREHOUSE_API_BASE", f"{BASE}/api/v1")
        import terminal.api_client as api_client
        importlib.reload(api_client)

        # Terminal stores an item...
        # The fresh live DB carries demo stock (Keyboard+Mouse already fill
        # A2 to 25/30), so 12 units correctly land on another shelf.
        data = api_client.store_product("Headphones", 12)
        assert data["quantity_stored"] == 12
        assert data["assigned_location"] not in ("RECEIVING", "A2")
        # ...and the webpage's view of the same backend shows it.
        rows = requests.get(f"{BASE}/api/v1/inventory", timeout=5).json()["data"]
        assert any(r["product"] == "Headphones" and r["quantity"] == 12 for r in rows)
        # Web-side dispatch; the terminal's locate sees the new quantity.
        r = requests.post(f"{BASE}/api/v1/inventory/dispatch",
                          json={"product_name": "Headphones", "quantity": 5}, timeout=5)
        assert r.json()["success"] is True
        located = api_client.locate_product("Headphones", 7)
        assert located["total_available"] == 7
        assert located["status"] == "CAN_BE_FULFILLED"
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
