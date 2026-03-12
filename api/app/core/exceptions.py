"""
Custom exception classes and centralized error handling.
"""
from __future__ import annotations

from typing import Any, Optional


class AppException(Exception):
    """Base application exception."""

    def __init__(
        self,
        message: str = "An unexpected error occurred",
        status_code: int = 500,
        detail: Optional[Any] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.detail = detail
        super().__init__(self.message)


class NotFoundError(AppException):
    def __init__(self, resource: str = "Resource", identifier: Any = None):
        msg = f"{resource} not found"
        if identifier:
            msg += f": {identifier}"
        super().__init__(message=msg, status_code=404)


class ConflictError(AppException):
    def __init__(self, message: str = "Resource already exists"):
        super().__init__(message=message, status_code=409)


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Not authenticated"):
        super().__init__(message=message, status_code=401)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Insufficient permissions"):
        super().__init__(message=message, status_code=403)


class ValidationError(AppException):
    def __init__(self, message: str = "Validation error", detail: Any = None):
        super().__init__(message=message, status_code=422, detail=detail)


class RateLimitError(AppException):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message=message, status_code=429)


class FileTooLargeError(AppException):
    def __init__(self, max_size_mb: int):
        super().__init__(
            message=f"File exceeds maximum size of {max_size_mb}MB",
            status_code=413,
        )


class UnsupportedFileTypeError(AppException):
    def __init__(self, extension: str):
        super().__init__(
            message=f"Unsupported file type: {extension}",
            status_code=415,
        )


class LLMError(AppException):
    """Raised when LLM call fails."""
    def __init__(self, message: str = "LLM service unavailable"):
        super().__init__(message=message, status_code=503)


class RetrievalError(AppException):
    """Raised when retrieval pipeline fails."""
    def __init__(self, message: str = "Retrieval failed"):
        super().__init__(message=message, status_code=500)
