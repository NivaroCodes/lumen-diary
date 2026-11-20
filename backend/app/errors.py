"""Единый формат ошибок API (без трассировок в теле ответа)."""
from __future__ import annotations


class ApiError(Exception):
    def __init__(self, status: int, error: str, message: str | None = None, field: str | None = None):
        super().__init__(message or error)
        self.status = status
        self.error = error
        self.message = message
        self.field = field

    def body(self) -> dict[str, str]:
        body = {"error": self.error}
        if self.field is not None:
            body["field"] = self.field
        if self.message is not None:
            body["message"] = self.message
        return body


def validation_error(field: str, message: str) -> ApiError:
    return ApiError(400, "validation_error", message, field)


def file_too_large(message: str) -> ApiError:
    return ApiError(413, "file_too_large", message, "photos")
