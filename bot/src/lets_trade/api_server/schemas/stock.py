"""주식 관련 스키마"""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class StockPriceResponse(BaseModel):
    """주식 현재가 응답"""

    symbol: str
    name: str
    price: int
    change: int
    change_rate: float
    volume: int
    open_price: int
    high_price: int
    low_price: int
    prev_close: int
    timestamp: datetime


class OrderBookResponse(BaseModel):
    """호가 정보 응답"""

    symbol: str
    ask_prices: list[int]  # 매도호가 (10단계)
    ask_volumes: list[int]  # 매도잔량
    bid_prices: list[int]  # 매수호가 (10단계)
    bid_volumes: list[int]  # 매수잔량
    timestamp: datetime


class StockTradeResponse(BaseModel):
    """체결 정보 응답"""

    symbol: str
    price: int
    volume: int
    trade_type: Literal["매수", "매도"]
    time: str


class StockTradeListResponse(BaseModel):
    """체결 목록 응답"""

    items: list[StockTradeResponse]
    count: int


class MultiPriceRequest(BaseModel):
    """복수 종목 시세 요청"""

    symbols: list[str]  # 최대 20종목


class MultiPriceResponse(BaseModel):
    """복수 종목 시세 응답"""

    prices: dict[str, StockPriceResponse]
    errors: dict[str, str]  # 종목코드 -> 에러 메시지
    timestamp: datetime
