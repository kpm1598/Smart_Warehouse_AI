"""Smart Warehouse AI — FastAPI application entry point.

One backend and one SQLite database serve BOTH the terminal client and
the web dashboard. The frontend is served by FastAPI itself (same origin).
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.config import API_PREFIX, FRONTEND_DIR
from backend.database import init_db
from backend.routes import ai_search, dashboard, inventory, products, warehouse
from backend.services.errors import AppError

app = FastAPI(title="Smart Warehouse AI", version="1.0.0")


@app.on_event("startup")
def _startup():
    init_db()


@app.exception_handler(AppError)
def app_error_handler(_request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.message, "error_code": exc.error_code},
    )


@app.exception_handler(RequestValidationError)
def validation_handler(_request: Request, exc: RequestValidationError):
    first = exc.errors()[0] if exc.errors() else {}
    message = first.get("msg", "Validation error")
    return JSONResponse(
        status_code=422,
        content={"success": False, "message": message, "error_code": "VALIDATION_ERROR"},
    )


@app.exception_handler(StarletteHTTPException)
def http_handler(_request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "message": str(exc.detail),
            "error_code": "HTTP_ERROR",
        },
    )


@app.get("/health")
def health():
    return {"success": True, "message": "ok", "data": {"status": "ok"}}


app.include_router(dashboard.router, prefix=API_PREFIX)
app.include_router(products.router, prefix=API_PREFIX)
app.include_router(inventory.router, prefix=API_PREFIX)
app.include_router(warehouse.router, prefix=API_PREFIX)
app.include_router(ai_search.router, prefix=API_PREFIX)

# Serve the web dashboard (must be mounted last so /api routes win).
app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
