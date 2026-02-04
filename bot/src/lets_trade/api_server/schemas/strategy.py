"""전략 관련 스키마"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class StrategySchema(BaseModel):
    """전략 정보"""

    id: int
    name: str
    description: Optional[str] = None
    strategy_type: str
    stock_codes: Optional[str] = None  # 콤마 구분
    parameters: Optional[dict] = None
    max_investment: Optional[int] = None
    max_loss_rate: Optional[int] = None  # 퍼센트
    take_profit_rate: Optional[int] = None  # 퍼센트
    is_active: bool
    priority: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StrategyListResponse(BaseModel):
    """전략 목록 응답"""

    items: list[StrategySchema]
    total: int
    active_count: int
    limit: int
    offset: int


class StrategyCreateRequest(BaseModel):
    """전략 생성 요청"""

    name: str
    description: Optional[str] = None
    strategy_type: str
    stock_codes: Optional[str] = None
    parameters: Optional[dict] = None
    max_investment: Optional[int] = None
    max_loss_rate: Optional[int] = None
    take_profit_rate: Optional[int] = None
    is_active: bool = False
    priority: int = 0


class StrategyUpdateRequest(BaseModel):
    """전략 수정 요청"""

    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[dict] = None
    stock_codes: Optional[str] = None
    max_investment: Optional[int] = None
    max_loss_rate: Optional[int] = None
    take_profit_rate: Optional[int] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None


class StrategyToggleResponse(BaseModel):
    """전략 토글 응답"""

    id: int
    is_active: bool
    updated_at: datetime
