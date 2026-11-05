"""Global exception handlers for structured error responses.

Registers handlers on the FastAPI app so every error — custom,
HTTP, validation, or unhandled — returns a consistent JSON envelope
with the request ID for traceability.
"""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from backend.app.exceptions import AppError, RateLimitError
from backend.app.logging_config import request_id_var

logger = logging.getLogger("agentos.errors")


def _error_response(status_code: int, code: str, message: str, request_id: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
            }
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    """Attach all global exception handlers to the app."""

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        req_id = request_id_var.get("")
        logger.warning(
            "AppError %s: %s",
            exc.code,
            exc.message,
            extra={"error_code": exc.code, "status_code": exc.status_code},
        )
        response = _error_response(exc.status_code, exc.code, exc.message, req_id)
        if isinstance(exc, RateLimitError):
            response.headers["Retry-After"] = str(exc.retry_after)
        return response

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        req_id = request_id_var.get("")
        code = {
            400: "BAD_REQUEST",
            401: "AUTHENTICATION_REQUIRED",
            403: "FORBIDDEN",
            404: "NOT_FOUND",
            405: "METHOD_NOT_ALLOWED",
            429: "RATE_LIMIT_EXCEEDED",
        }.get(exc.status_code, "HTTP_ERROR")
        return _error_response(exc.status_code, code, str(exc.detail), req_id)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        req_id = request_id_var.get("")
        errors = exc.errors()
        if errors:
            first = errors[0]
            loc = " → ".join(str(p) for p in first.get("loc", []))
            msg = f"{loc}: {first.get('msg', 'invalid')}"
        else:
            msg = "Request validation failed"
        return _error_response(422, "VALIDATION_ERROR", msg, req_id)

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        req_id = request_id_var.get("")
        logger.exception("Unhandled exception", extra={"error_type": type(exc).__name__})
        return _error_response(500, "INTERNAL_ERROR", "An unexpected error occurred", req_id)
