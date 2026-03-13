"""Common utilities for the API layer."""
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from typing import Any, Dict


def success_response(data: Any = None, message: str = "Success") -> JSONResponse:
    """Return a standardized success response."""
    return JSONResponse(content={
        "success": True,
        "message": message,
        "data": data
    })


def error_response(
    status_code: int,
    message: str,
    details: Any = None
) -> HTTPException:
    """Return a standardized error response.

    Args:
        status_code: HTTP status code
        message: Human-readable error message
        details: Optional additional error details (dict, string, etc.)

    Returns:
        HTTPException with consistent error format
    """
    content = {
        "success": False,
        "message": message,
    }
    if details:
        content["details"] = details
    return HTTPException(status_code=status_code, detail=content)


def api_success(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Helper to build success dict for manual JSONResponse."""
    return {
        "success": True,
        "message": message,
        "data": data
    }


def api_error(message: str, details: Any = None) -> Dict[str, Any]:
    """Helper to build error dict."""
    error = {"message": message}
    if details:
        error["details"] = details
    return error
