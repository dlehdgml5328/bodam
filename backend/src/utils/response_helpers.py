"""Response helper utilities for consistent API responses."""

from __future__ import annotations

from typing import Any, Generic, TypeVar
from pydantic import BaseModel
from fastapi import status
from fastapi.responses import JSONResponse

from .pagination import PaginatedResponse

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response format."""

    success: bool
    data: T | None = None
    message: str | None = None
    error_code: str | None = None


class ErrorDetail(BaseModel):
    """Detailed error information."""

    code: str
    message: str
    field: str | None = None


class ErrorResponse(BaseModel):
    """Error response format."""

    success: bool = False
    message: str
    error_code: str
    details: list[ErrorDetail] | None = None


def success_response(
    data: Any = None,
    message: str | None = None,
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    """Create a successful API response."""
    response_data = ApiResponse(
        success=True,
        data=data,
        message=message,
    )
    return JSONResponse(
        content=response_data.dict(exclude_none=True),
        status_code=status_code,
    )


def error_response(
    message: str,
    error_code: str = "INTERNAL_ERROR",
    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    """Create an error API response."""
    response_data = ErrorResponse(
        message=message,
        error_code=error_code,
        details=details,
    )
    return JSONResponse(
        content=response_data.dict(exclude_none=True),
        status_code=status_code,
    )


def validation_error_response(
    message: str = "입력값이 올바르지 않습니다.",
    details: list[ErrorDetail] | None = None,
) -> JSONResponse:
    """Create a validation error response."""
    return error_response(
        message=message,
        error_code="VALIDATION_ERROR",
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        details=details,
    )


def not_found_response(
    message: str = "요청한 리소스를 찾을 수 없습니다.",
    error_code: str = "NOT_FOUND",
) -> JSONResponse:
    """Create a not found error response."""
    return error_response(
        message=message,
        error_code=error_code,
        status_code=status.HTTP_404_NOT_FOUND,
    )


def unauthorized_response(
    message: str = "인증이 필요합니다.",
    error_code: str = "UNAUTHORIZED",
) -> JSONResponse:
    """Create an unauthorized error response."""
    return error_response(
        message=message,
        error_code=error_code,
        status_code=status.HTTP_401_UNAUTHORIZED,
    )


def forbidden_response(
    message: str = "접근 권한이 없습니다.",
    error_code: str = "FORBIDDEN",
) -> JSONResponse:
    """Create a forbidden error response."""
    return error_response(
        message=message,
        error_code=error_code,
        status_code=status.HTTP_403_FORBIDDEN,
    )


def paginated_response(
    paginated_data: PaginatedResponse[T],
    message: str | None = None,
    status_code: int = status.HTTP_200_OK,
) -> JSONResponse:
    """Create a paginated API response."""
    response_data = ApiResponse(
        success=True,
        data=paginated_data.dict(),
        message=message,
    )
    return JSONResponse(
        content=response_data.dict(exclude_none=True),
        status_code=status_code,
    )


def created_response(
    data: Any = None,
    message: str = "리소스가 성공적으로 생성되었습니다.",
) -> JSONResponse:
    """Create a created response."""
    return success_response(
        data=data,
        message=message,
        status_code=status.HTTP_201_CREATED,
    )


def no_content_response() -> JSONResponse:
    """Create a no content response."""
    return JSONResponse(
        content=None,
        status_code=status.HTTP_204_NO_CONTENT,
    )