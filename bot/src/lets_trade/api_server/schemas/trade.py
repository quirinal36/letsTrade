"""거래 관련 스키마"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal

from pydantic import BaseModel


class TradeSchema(BaseModel):
    """거래 내역"""

    id: int
    order_no: str
    stock_code: str
    stock_name: str
    order_type: Literal["buy", "sell"]
    status: Literal["pending", "executed", "partial", "cancelled", "rejected"]
    quantity: int
    price: Decimal
    executed_quantity: int
    executed_price: Optional[Decimal] = None
    strategy_id: Optional[int] = None
    signal_id: Optional[int] = None
    notes: Optional[str] = None
    executed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TradeSummary(BaseModel):
    """거래 요약"""

    total_count: int
    buy_count: int
    sell_count: int
    executed_count: int
    pending_count: int


class TradeListResponse(BaseModel):
    """거래 목록 응답"""

    items: list[TradeSchema]
    total: int
    limit: int
    offset: int
    summary: TradeSummary
