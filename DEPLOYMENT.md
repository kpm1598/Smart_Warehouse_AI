# Smart Warehouse AI — Web Deployment (Render, free tier)

## ✅ LIVE (deployed 17 Nov 2026)

- **Public URL: https://smart-warehouse-ai-3iu5.onrender.com**
- GitHub repo: https://github.com/kpm1598/Smart_Warehouse_AI (branch `main`)
- Render service: `smart-warehouse-ai` (free plan, Blueprint-managed from `render.yaml`; every push to `main` auto-redeploys)
- Verified live after deploy: dashboard, `/health`, summary, store, locate, dispatch, warehouse map and AI comparison all working.
- Terminal against the live backend (optional, PowerShell):
  `$env:WAREHOUSE_API_BASE = "https://smart-warehouse-ai-3iu5.onrender.com/api/v1"` then run the terminal as usual.

This project is ready to deploy as a single web service. The FastAPI backend
serves the web dashboard itself, so **one deployment = the whole app**
(backend + webpage + database). The terminal client stays a local program;
it is not part of the web deploy.

## How it deploys on Render

1. Put this project in a GitHub repository (files at the repo root:
   `backend/`, `frontend/`, `terminal/`, `requirements.txt`, `render.yaml`).
2. On [render.com](https://render.com): **New → Blueprint** (or New → Web
   Service) and connect that GitHub repo.
3. Render reads `render.yaml` automatically:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - Health check: `/health`
   - Env vars set for you: `PYTHON_VERSION=3.12.3`,
     `WAREHOUSE_DB_PATH=data/warehouse.db`
4. Wait for the first build to finish. Render gives you a public URL like
   `https://smart-warehouse-ai.onrender.com`.

That's it — no settings to type in by hand. `Procfile` and `runtime.txt`
are included as well, so the same folder also works on other Python hosts
that use those conventions.

## Using the live app

Anyone with the URL just opens it in a browser — **no Python, no install,
no files to run**, which is exactly what fixes the "won't open on another
system" problem (Windows Smart App Control / PowerShell script blocks only
affect locally downloaded files, never a web page). All pages work as they
do locally: Dashboard, Inventory, Store, Locate, Dispatch, Warehouse Map
and the AI Comparison page, because the same backend serves both the pages
and the `/api/v1` APIs.

## Honest limits of the free tier (read before a demo)

- **The service sleeps.** On Render's free plan the app spins down after
  ~15 minutes without visitors. The next visit then takes roughly
  **30–60 seconds** to wake up before the page loads. Open the URL a
  couple of minutes before a presentation so it's awake.
- **The database is temporary.** Free-tier storage is ephemeral: the
  SQLite file is wiped on every redeploy, restart or spin-down cycle, and
  the app automatically re-creates it with the seeded demo data
  (Keyboard ×10 + Mouse ×15 at A2, USB Cable ×20 at A1). Anything stored
  during a demo can disappear later. Perfect for a college demo;
  **not suitable for real warehouse records.**
- **No login / no authentication.** Anyone who has the URL can view,
  store and dispatch stock. Treat the link as a public demo link only.
- **One shared database.** Every visitor sees and changes the same
  inventory (same behaviour as the local version's single database).

## Optional: point the local terminal at the hosted backend

The terminal client reads its server address from the `WAREHOUSE_API_BASE`
environment variable (default `http://127.0.0.1:8000/api/v1`). To use the
hosted copy from a laptop instead of a local backend, in PowerShell:

```powershell
$env:WAREHOUSE_API_BASE = "https://smart-warehouse-ai.onrender.com/api/v1"
.\run_terminal.bat
```

(Use your real Render URL.) The terminal then works against the same live
database as the webpage. Remember the free-tier limits above: if the
service is asleep, the first terminal action may time out — open the URL
in a browser first to wake it.

## Local running (unchanged)

Nothing about local use changes: `run_backend.bat` + `run_terminal.bat`,
or `py -m uvicorn backend.main:app --host 127.0.0.1 --port 8000` and the
dashboard at http://127.0.0.1:8000/ — see README.md.
