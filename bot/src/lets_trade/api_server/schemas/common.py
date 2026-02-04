"""공통 스키마 정의"""

from datetime import datetime
from typing import Generic, TypeVar, Optional

from pydantic import BaseModel, Field


T = TypeVar("T")


class BaseResponse(BaseModel):
    """기본 응답 래퍼"""

    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class PaginatedResponse(BaseModel, Generic[T]):
    """페이징 응답 래퍼"""

    items: list[T]
    total: int
    limit: int
    offset: int
    has_more: bool


class ErrorResponse(BaseModel):
    """에러 응답"""

    success: bool = False
    error_code: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ErrorCode:
    """에러 코드 상수"""

    # 클라이언트 에러 (4xx)
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_SYMBOL = "INVALID_SYMBOL"
    INVALID_ORDER = "INVALID_ORDER"
    UNAUTHORIZED = "UNAUTHORIZED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    ORDER_LIMIT_EXCEEDED = "ORDER_LIMIT_EXCEEDED"
    INSUFFICIENT_BALANCE = "INSUFFICIENT_BALANCE"

    # 서버 에러 (5xx)
    BROKER_API_ERROR = "BROKER_API_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    SUPABASE_SYNC_ERROR = "SUPABASE_SYNC_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
