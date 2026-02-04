"""전략 프레임워크 베이스 클래스"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional

import pandas as pd


class SignalType(Enum):
    """시그널 유형"""
    BUY = "buy"
    SELL = "sell"
    HOLD = "hold"


@dataclass
class Signal:
    """매매 시그널"""
    signal_type: SignalType
    symbol: str
    price: float
    quantity: Optional[int] = None
    strength: float = 0.0      # 시그널 강도 (0~1)
    confidence: float = 0.0    # 신뢰도 (0~1)
    reason: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    @property
    def is_buy(self) -> bool:
        return self.signal_type == SignalType.BUY

    @property
    def is_sell(self) -> bool:
        return self.signal_type == SignalType.SELL

    @property
    def is_hold(self) -> bool:
        return self.signal_type == SignalType.HOLD


@dataclass
class StrategyConfig:
    """전략 설정"""
    name: str
    description: str = ""
    parameters: dict = field(default_factory=dict)
    symbols: list[str] = field(default_factory=list)
    max_investment: int = 1_000_000  # 최대 투자금
    max_loss_rate: float = 5.0       # 최대 손실률 (%)
    take_profit_rate: float = 10.0   # 익절 기준 (%)
    is_active: bool = True


class Strategy(ABC):
    """
    전략 베이스 클래스

    모든 매매 전략은 이 클래스를 상속받아 구현합니다.
    """

    def __init__(self, config: StrategyConfig):
        self.config = config
        self._is_initialized = False

    @property
    def name(self) -> str:
        return self.config.name

    @property
    def parameters(self) -> dict:
        return self.config.parameters

    @property
    def is_active(self) -> bool:
        return self.config.is_active

    def activate(self) -> None:
        """전략 활성화"""
        self.config.is_active = True

    def deactivate(self) -> None:
        """전략 비활성화"""
        self.config.is_active = False

    @abstractmethod
    def initialize(self) -> None:
        """
        전략 초기화

        전략 실행에 필요한 데이터 로드, 지표 계산 등을 수행합니다.
        """
        pass

    @abstractmethod
    def generate_signal(self, data: pd.DataFrame) -> Signal:
        """
        시그널 생성

        Args:
            data: OHLCV 데이터 (columns: open, high, low, close, volume)

        Returns:
            Signal: 매매 시그널
        """
        pass

    @abstractmethod
    def calculate_position_size(self, signal: Signal, available_cash: float) -> int:
        """
        포지션 크기 계산

        Args:
            signal: 매매 시그널
            available_cash: 사용 가능 현금

        Returns:
            int: 주문 수량
        """
        pass

    def validate_signal(self, signal: Signal) -> bool:
        """
        시그널 유효성 검증

        Args:
            signal: 매매 시그널

        Returns:
            bool: 유효 여부
        """
        if signal.is_hold:
            return True

        if signal.price <= 0:
            return False

        if signal.strength < 0 or signal.strength > 1:
            return False

        return True

    def on_order_executed(self, order_result: Any) -> None:
        """
        주문 체결 콜백

        Args:
            order_result: 주문 결과
        """
        pass

    def on_error(self, error: Exception) -> None:
        """
        에러 발생 콜백

        Args:
            error: 발생한 예외
        """
        pass

    def __repr__(self) -> str:
        return f"Strategy({self.name}, active={self.is_active})"


class StrategyRegistry:
    """전략 레지스트리 (싱글톤)"""

    _instance = None
    _strategies: dict[str, type[Strategy]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def register(cls, name: str):
        """전략 등록 데코레이터"""
        def decorator(strategy_class: type[Strategy]):
            cls._strategies[name] = strategy_class
            return strategy_class
        return decorator

    @classmethod
    def get(cls, name: str) -> Optional[type[Strategy]]:
        """등록된 전략 클래스 조회"""
        return cls._strategies.get(name)

    @classmethod
    def list_strategies(cls) -> list[str]:
        """등록된 전략 목록"""
        return list(cls._strategies.keys())

    @classmethod
    def create(cls, name: str, config: StrategyConfig) -> Optional[Strategy]:
        """전략 인스턴스 생성"""
        strategy_class = cls.get(name)
        if strategy_class:
            return strategy_class(config)
        return None
