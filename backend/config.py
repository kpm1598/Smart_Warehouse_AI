"""Application configuration.

The database lives at <project>/data/warehouse.db by default and can be
overridden with the WAREHOUSE_DB_PATH environment variable (tests use a
temporary database so they never touch the real demo database).
"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"

_default_db = PROJECT_ROOT / "data" / "warehouse.db"
DB_PATH = Path(os.environ.get("WAREHOUSE_DB_PATH", str(_default_db)))
DATABASE_URL = f"sqlite:///{DB_PATH}"

API_PREFIX = "/api/v1"
START_LOCATION = "RECEIVING"
