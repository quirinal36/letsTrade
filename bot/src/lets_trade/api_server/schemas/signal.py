"""시그널 관련 스키마"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Literal

from pydantic import BaseModel


class SignalSchema(BaseModel):
    """시그널 정보"""

    id: int
    strategy_id: int
    stock_code: str
    stock_name: str
    signal_type: Literal["buy", "sell", "hold"]
    status: Literal["pending", "executed", "ignored", "expired"]
    price: Decimal
    quantity: Optional[int] = None
    strength: Decimal  # 0-100
    confidence: Decimal  # 0-100
    analysis_data: Optional[dict] = None
    trade_id: Optional[int] = None
    reason: Optional[str] = None
    executed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SignalListResponse(BaseModel):
    """시그널 목록 응답"""

    items: list[SignalSchema]
    total: int
    limit: int
    offset: int


class SignalStatsResponse(BaseModel):
    """시그널 통계"""

    strategy_id: int
    strategy_name: str
    total_signals: int
    executed_signals: int
    buy_signals: int
    sell_signals: int
    avg_strength: float
    avg_confidence: float
    period_days: int
