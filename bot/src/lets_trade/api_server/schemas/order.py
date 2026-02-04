"""주문 관련 스키마"""

from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field


class BuyOrderRequest(BaseModel):
    """매수 주문 요청"""

    symbol: str
    quantity: int = Field(..., gt=0)
    price: int = Field(default=0, ge=0)  # 0이면 시장가
    order_type: Literal["limit", "market"] = "limit"
    strategy_id: Optional[int] = None
    signal_id: Optional[int] = None
    notes: Optional[str] = None


class SellOrderRequest(BaseModel):
    """매도 주문 요청"""

    symbol: str
    quantity: int = Field(..., gt=0)
    price: int = Field(default=0, ge=0)  # 0이면 시장가
    order_type: Literal["limit", "market"] = "limit"
    strategy_id: Optional[int] = None
    signal_id: Optional[int] = None
    notes: Optional[str] = None


class ModifyOrderRequest(BaseModel):
    """주문 정정 요청"""

    symbol: str
    quantity: int = Field(..., gt=0)
    price: int = Field(..., gt=0)


class CancelOrderRequest(BaseModel):
    """주문 취소 요청"""

    symbol: str
    quantity: int = Field(..., gt=0)


class OrderResultResponse(BaseModel):
    """주문 결과 응답"""

    order_no: str
    symbol: str
    side: Literal["매수", "매도", "정정", "취소"]
    quantity: int
    price: int
    order_time: str
    status: str
    trade_id: Optional[int] = None  # 생성된 Trade 레코드 ID


class BrokerOrderSchema(BaseModel):
    """브로커 주문 내역"""

    order_no: str
    symbol: str
    name: str
    side: str
    order_qty: int
    exec_qty: int
    order_price: int
    exec_price: int
    status: str
    order_time: str


class BrokerOrderListResponse(BaseModel):
    """브로커 주문 목록 응답"""

    items: list[BrokerOrderSchema]
    count: int
    timestamp: datetime
