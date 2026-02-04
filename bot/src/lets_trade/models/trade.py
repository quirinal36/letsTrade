"""거래 내역 모델"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from sqlalchemy import String, Integer, Numeric, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class OrderType(str, Enum):
    """주문 유형"""
    BUY = "buy"      # 매수
    SELL = "sell"    # 매도


class OrderStatus(str, Enum):
    """주문 상태"""
    PENDING = "pending"        # 대기
    EXECUTED = "executed"      # 체결
    PARTIAL = "partial"        # 부분체결
    CANCELLED = "cancelled"    # 취소
    REJECTED = "rejected"      # 거부


class Trade(Base, TimestampMixin):
    """거래 내역 테이블"""
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 주문 정보
    order_no: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    stock_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    stock_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # 주문 유형 및 상태
    order_type: Mapped[str] = mapped_column(String(10), nullable=False)  # buy/sell
    status: Mapped[str] = mapped_column(String(20), nullable=False, default=OrderStatus.PENDING)

    # 수량 및 가격
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    executed_quantity: Mapped[int] = mapped_column(Integer, default=0)
    executed_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)

    # 전략 정보
    strategy_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    signal_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # 추가 정보
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<Trade {self.order_no}: {self.order_type} {self.stock_code} x{self.quantity}>"
