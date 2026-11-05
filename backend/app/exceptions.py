"""Custom exception hierarchy for structured error responses.

All API errors inherit from AppError so global handlers can catch
them and return a consistent JSON envelope:

    {"error": {"code": "RATE_LIMIT_EXCEEDED", "message": "...", "request_id": "..."}}

HTTP status codes are attached to each exception class so handlers
don't need a mapping table.
"""


class AppError(Exception):
    """Base for all application errors."""

    status_code: int = 500
    code: str = "INTERNAL_ERROR"

    def __init__(self, message: str = "An unexpected error occurred"):
        self.message = message
        super().__init__(message)


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"

    def __init__(self, resource: str = "Resource", identifier: str = ""):
        detail = f"{resource} not found" if not identifier else f"{resource} '{identifier}' not found"
        super().__init__(detail)


class ValidationError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"

    def __init__(self, message: str = "Invalid input"):
        super().__init__(message)


class RateLimitError(AppError):
    status_code = 429
    code = "RATE_LIMIT_EXCEEDED"

    def __init__(self, retry_after: int = 60):
        self.retry_after = retry_after
        super().__init__(f"Rate limit exceeded. Retry after {retry_after}s")


class AuthenticationError(AppError):
    status_code = 401
    code = "AUTHENTICATION_REQUIRED"

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message)


class AuthorizationError(AppError):
    status_code = 403
    code = "FORBIDDEN"

    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message)


class ServiceUnavailableError(AppError):
    status_code = 503
    code = "SERVICE_UNAVAILABLE"

    def __init__(self, service: str = "Service"):
        super().__init__(f"{service} is temporarily unavailable")


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"

    def __init__(self, message: str = "Resource conflict"):
        super().__init__(message)
