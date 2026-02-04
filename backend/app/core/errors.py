"""Application error types."""

from typing import Any


class AppError(Exception):
    """Base application error."""

    def __init__(
        self,
        message: str,
        code: str = "APP_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppError):
    """Resource not found error."""

    def __init__(self, resource: str, identifier: str | None = None):
        message = f"{resource} not found"
        if identifier:
            message = f"{resource} with id '{identifier}' not found"
        super().__init__(message, code="NOT_FOUND", status_code=404)


class ForbiddenError(AppError):
    """Permission denied error."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, code="FORBIDDEN", status_code=403)


class ValidationError(AppError):
    """Validation error."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, code="VALIDATION_ERROR", status_code=422, details=details)


class ConflictError(AppError):
    """Resource conflict error."""

    def __init__(self, message: str):
        super().__init__(message, code="CONFLICT", status_code=409)


class UnauthorizedError(AppError):
    """Authentication required error."""

    def __init__(self, message: str = "Authentication required"):
        super().__init__(message, code="UNAUTHORIZED", status_code=401)
