"""시그널 모델"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from sqlalchemy import String, Integer, Numeric, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class SignalType(str, Enum):
    """시그널 유형"""
    BUY = "buy"    # 매수 시그널
    SELL = "sell"  # 매도 시그널
    HOLD = "hold"  # 홀드 시그널


class SignalStatus(str, Enum):
    """시그널 상태"""
    PENDING = "pending"    # 대기 (처리 전)
    EXECUTED = "executed"  # 실행됨
    IGNORED = "ignored"    # 무시됨
    EXPIRED = "expired"    # 만료됨


class Signal(Base, TimestampMixin):
    """시그널 로그 테이블"""
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 전략 연결
    strategy_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # 종목 정보
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    stock_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # 시그널 정보
    signal_type: Mapped[str] = mapped_column(String(10), nullable=False)  # buy/sell/hold
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=SignalStatus.PENDING)

    # 추천 가격/수량
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    quantity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 시그널 강도 및 신뢰도
    strength: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)  # 0-100
    confidence: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0)  # 0-100

    # 분석 데이터 (JSON)
    analysis_data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # 실행 정보
    trade_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # 메모
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 시그널 발생 이유

    def __repr__(self) -> str:
        return f"<Signal {self.signal_type.upper()} {self.stock_code} @ {self.price}>"
