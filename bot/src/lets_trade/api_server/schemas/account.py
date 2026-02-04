"""계좌 관련 스키마"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PositionSchema(BaseModel):
    """보유 종목 정보"""

    symbol: str
    name: str
    quantity: int
    avg_price: float
    current_price: int
    total_cost: float
    market_value: int
    profit_loss: float
    profit_rate: float


class BalanceResponse(BaseModel):
    """계좌 잔고 응답"""

    deposit: int  # 예수금
    available: int  # 주문가능금액
    total_eval: int  # 총평가금액
    total_profit: float  # 총평가손익
    profit_rate: float  # 총수익률(%)
    d1_deposit: Optional[int] = None  # D+1 예수금
    d2_deposit: Optional[int] = None  # D+2 예수금
    substitute: Optional[int] = None  # 대용금액
    timestamp: datetime


class PositionsListResponse(BaseModel):
    """보유 종목 목록 응답"""

    positions: list[PositionSchema]
    count: int
    timestamp: datetime
