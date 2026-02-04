"""전략 모델"""

from enum import Enum
from typing import Optional
from sqlalchemy import String, Integer, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class StrategyType(str, Enum):
    """전략 유형"""
    MANUAL = "manual"                    # 수동
    MOVING_AVERAGE = "moving_average"    # 이동평균선
    RSI = "rsi"                          # RSI
    MACD = "macd"                        # MACD
    BOLLINGER = "bollinger"              # 볼린저밴드
    CUSTOM = "custom"                    # 사용자 정의


class Strategy(Base, TimestampMixin):
    """전략 설정 테이블"""
    __tablename__ = "strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 전략 기본 정보
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    strategy_type: Mapped[str] = mapped_column(String(50), nullable=False)

    # 대상 종목 (null이면 전체)
    stock_codes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # 콤마 구분

    # 전략 파라미터 (JSON)
    parameters: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    # 리스크 관리
    max_investment: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 최대 투자금액
    max_loss_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)   # 최대 손실률 (%)
    take_profit_rate: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) # 익절률 (%)

    # 상태
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)  # 우선순위

    def __repr__(self) -> str:
        return f"<Strategy {self.name} ({self.strategy_type})>"
