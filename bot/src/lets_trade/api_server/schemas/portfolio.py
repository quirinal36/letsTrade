"""포트폴리오 관련 스키마"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel


class PortfolioPositionSchema(BaseModel):
    """포트폴리오 포지션"""

    id: int
    stock_code: str
    stock_name: str
    quantity: int
    avg_price: Decimal
    current_price: Decimal
    total_cost: Decimal
    market_value: Decimal
    profit_loss: Decimal
    profit_loss_rate: Decimal
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class PortfolioListResponse(BaseModel):
    """포트폴리오 목록 응답"""

    items: list[PortfolioPositionSchema]
    total: int
    limit: int
    offset: int


class PortfolioSummaryResponse(BaseModel):
    """포트폴리오 요약 응답"""

    total_value: Decimal
    total_cost: Decimal
    total_profit: Decimal
    profit_rate: Decimal
    position_count: int
    today_trade_count: int
    timestamp: datetime


class SyncResultResponse(BaseModel):
    """동기화 결과 응답"""

    synced_count: int
    added: int
    updated: int
    removed: int
    timestamp: datetime
