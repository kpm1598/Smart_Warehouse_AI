"""Consistent API response wrapper (TDD section 8.6)."""
from fastapi.responses import JSONResponse


def success(data=None, message="Operation completed successfully", status_code=200):
    return JSONResponse(
        status_code=status_code,
        content={"success": True, "message": message, "data": data},
    )


def failure(message, error_code, status_code):
    return JSONResponse(
        status_code=status_code,
        content={"success": False, "message": message, "error_code": error_code},
    )
