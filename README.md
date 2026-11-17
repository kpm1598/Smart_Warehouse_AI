# Smart Warehouse AI

Local-first warehouse inventory and storage management system.
One FastAPI backend + one SQLite database, shared by a Python terminal
client and a web dashboard. Storage allocation uses **Greedy Best-First
Search**; warehouse navigation uses **Depth-Limited Search** — both
implemented manually in Python (no pathfinding library).

## Features

- Store stock with AI allocation (a batch must fit completely into one
  shelf — no splitting, no partial stores; the same product may live on
  several shelves from separate batches)
- Fixed shelf capacities (30 / 50 / 100), enforced transactionally
- Locate products with fulfilment / shortage check
- Atomic stock dispatch across locations (nearest-to-RECEIVING first)
- Stock movement history (IN / OUT) that is never deleted
- Warehouse map: RECEIVING + 3x3 shelves A1–C3, pathway blocking
  (A2↔B2 starts blocked; alternative routes exist)
- AI comparison page: Greedy vs DLS on the same navigation problem,
  with real measured nodes explored, path distance and execution time
- Terminal and web stay in sync because both use the same API and database

## Requirements

- Windows with Python 3.10+ (commands below use the `py` launcher)
- No paid services, no internet needed after installing packages

## Install (Windows PowerShell, from the project folder)

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
py -m pip install -r requirements.txt
```

## Run

**Terminal 1 — backend** (or double-click `run_backend.bat`):

```powershell
py -m uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

On first start the database `data\warehouse.db` is created automatically,
the warehouse layout is seeded, and demo stock (Keyboard, Mouse, USB Cable)
is stored through the real allocation service.

**Web dashboard:** open http://127.0.0.1:8000/ in your browser
(the backend serves the frontend itself — nothing else to start).
API docs: http://127.0.0.1:8000/docs

**Terminal 2 — terminal client** (or double-click `run_terminal.bat`):

```powershell
py -m terminal.main
```

## Tests

```powershell
py -m pytest tests\ -q
```

Tests run against a temporary database and never touch `data\warehouse.db`.

## Warehouse layout

```
          RECEIVING
         /    |     \
       A1 —— A2 —— A3
       |     ✕     |        ✕ = A2↔B2 blocked at start
       B1 —— B2 —— B3
       |     |     |
       C1 —— C2 —— C3
```

Capacities: A1 50, A2 30, A3 100, B1 100, B2 50, B3 30, C1 30, C2 100, C3 50.

## Project structure

```
backend/    FastAPI app: models, schemas, routes, services, algorithms, seed
terminal/   Menu-driven terminal client (talks to the backend API only)
frontend/   Web dashboard (served by FastAPI, same origin)
data/       warehouse.db (SQLite, auto-created + seeded on first run)
tests/      pytest suite (temporary DB)
```

Environment overrides: `WAREHOUSE_DB_PATH` (database file),
`WAREHOUSE_API_BASE` (terminal's API base URL).

## Notes / limitations

- Local MVP: no login/authentication — do not expose port 8000 publicly.
- Greedy Best-First Search returns an AI-selected *suitable* location,
  not a mathematically optimal one (that is a property of the algorithm).
- DLS result CUTOFF means "not found within the depth limit", not
  "does not exist".
- Aarohi / Ollama integration is intentionally not included (future phase).
