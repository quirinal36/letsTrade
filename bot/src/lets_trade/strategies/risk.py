"""리스크 관리 모듈"""

from dataclasses import dataclass, field
from datetime import datetime, date
from enum import Enum
from typing import Optional


class StopType(Enum):
    """손절/익절 유형"""
    FIXED = "fixed"           # 고정 비율
    TRAILING = "trailing"     # 트레일링 스탑
    ATR = "atr"               # ATR 기반


@dataclass
class RiskConfig:
    """리스크 관리 설정"""
    # 손절/익절
    stop_loss_rate: float = 3.0       # 손절선 (%)
    take_profit_rate: float = 5.0     # 익절선 (%)
    stop_type: StopType = StopType.FIXED
    trailing_stop_rate: float = 2.0   # 트레일링 스탑 비율 (%)

    # 자금 관리
    max_position_rate: float = 10.0   # 1회 거래 최대 금액 (총자산 대비 %)
    max_stock_weight: float = 20.0    # 종목당 최대 비중 (%)
    max_total_position: float = 80.0  # 최대 투자 비중 (%)

    # 일일 제한
    daily_max_loss_rate: float = 5.0  # 일일 최대 손실 (%)
    daily_max_trades: int = 10        # 일일 최대 거래 횟수


@dataclass
class PositionState:
    """포지션 상태"""
    symbol: str
    entry_price: float
    current_price: float
    quantity: int
    highest_price: float = 0.0  # 트레일링 스탑용
    entry_date: datetime = field(default_factory=datetime.now)

    @property
    def profit_rate(self) -> float:
        """현재 수익률 (%)"""
        if self.entry_price <= 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price * 100

    @property
    def market_value(self) -> float:
        """평가금액"""
        return self.current_price * self.quantity


@dataclass
class DailyStats:
    """일일 통계"""
    date: date
    start_capital: float
    current_capital: float
    trade_count: int = 0
    profit_loss: float = 0.0

    @property
    def daily_return(self) -> float:
        """일일 수익률 (%)"""
        if self.start_capital <= 0:
            return 0.0
        return (self.current_capital - self.start_capital) / self.start_capital * 100


class RiskManager:
    """
    리스크 관리자

    손절/익절, 포지션 사이징, 일일 제한 등을 관리합니다.
    """

    def __init__(self, config: Optional[RiskConfig] = None):
        self.config = config or RiskConfig()
        self.positions: dict[str, PositionState] = {}
        self.daily_stats: Optional[DailyStats] = None
        self._is_trading_halted = False

    def initialize_daily(self, capital: float) -> None:
        """일일 통계 초기화 (매일 장 시작 전 호출)"""
        self.daily_stats = DailyStats(
            date=date.today(),
            start_capital=capital,
            current_capital=capital,
        )
        self._is_trading_halted = False

    def update_capital(self, current_capital: float) -> None:
        """현재 자본 업데이트"""
        if self.daily_stats:
            self.daily_stats.current_capital = current_capital
            self.daily_stats.profit_loss = current_capital - self.daily_stats.start_capital

    # ==================== 손절/익절 ====================

    def check_stop_loss(self, position: PositionState) -> bool:
        """
        손절 조건 확인

        Args:
            position: 포지션 상태

        Returns:
            bool: 손절 필요 여부
        """
        if self.config.stop_type == StopType.TRAILING:
            return self._check_trailing_stop(position)

        return position.profit_rate <= -self.config.stop_loss_rate

    def check_take_profit(self, position: PositionState) -> bool:
        """
        익절 조건 확인

        Args:
            position: 포지션 상태

        Returns:
            bool: 익절 필요 여부
        """
        return position.profit_rate >= self.config.take_profit_rate

    def _check_trailing_stop(self, position: PositionState) -> bool:
        """트레일링 스탑 확인"""
        if position.current_price > position.highest_price:
            position.highest_price = position.current_price

        if position.highest_price <= 0:
            return False

        drop_from_high = (
            (position.highest_price - position.current_price)
            / position.highest_price * 100
        )
        return drop_from_high >= self.config.trailing_stop_rate

    def should_close_position(self, position: PositionState) -> tuple[bool, str]:
        """
        포지션 청산 필요 여부 확인

        Args:
            position: 포지션 상태

        Returns:
            tuple[bool, str]: (청산 필요 여부, 사유)
        """
        if self.check_stop_loss(position):
            return True, "손절"

        if self.check_take_profit(position):
            return True, "익절"

        return False, ""

    # ==================== 포지션 사이징 ====================

    def calculate_position_size(
        self,
        price: float,
        total_capital: float,
        available_cash: float,
    ) -> int:
        """
        포지션 크기 계산

        Args:
            price: 주문 가격
            total_capital: 총 자산
            available_cash: 사용 가능 현금

        Returns:
            int: 주문 수량
        """
        if price <= 0:
            return 0

        # 1회 거래 최대 금액
        max_order_amount = total_capital * (self.config.max_position_rate / 100)

        # 사용 가능 현금 제한
        max_order_amount = min(max_order_amount, available_cash)

        # 수량 계산
        quantity = int(max_order_amount / price)

        return max(0, quantity)

    def check_position_weight(
        self,
        symbol: str,
        add_amount: float,
        total_capital: float,
    ) -> bool:
        """
        종목 비중 확인

        Args:
            symbol: 종목코드
            add_amount: 추가 투자 금액
            total_capital: 총 자산

        Returns:
            bool: 투자 가능 여부
        """
        current_position = self.positions.get(symbol)
        current_amount = current_position.market_value if current_position else 0

        new_weight = (current_amount + add_amount) / total_capital * 100
        return new_weight <= self.config.max_stock_weight

    def check_total_exposure(
        self,
        add_amount: float,
        total_capital: float,
    ) -> bool:
        """
        총 투자 비중 확인

        Args:
            add_amount: 추가 투자 금액
            total_capital: 총 자산

        Returns:
            bool: 투자 가능 여부
        """
        current_exposure = sum(p.market_value for p in self.positions.values())
        new_exposure = (current_exposure + add_amount) / total_capital * 100
        return new_exposure <= self.config.max_total_position

    # ==================== 일일 제한 ====================

    def check_daily_loss_limit(self) -> bool:
        """
        일일 최대 손실 제한 확인

        Returns:
            bool: 거래 가능 여부 (False면 거래 중단)
        """
        if self.daily_stats is None:
            return True

        if self.daily_stats.daily_return <= -self.config.daily_max_loss_rate:
            self._is_trading_halted = True
            return False

        return True

    def check_daily_trade_limit(self) -> bool:
        """
        일일 거래 횟수 제한 확인

        Returns:
            bool: 거래 가능 여부
        """
        if self.daily_stats is None:
            return True

        return self.daily_stats.trade_count < self.config.daily_max_trades

    def record_trade(self) -> None:
        """거래 기록 (횟수 증가)"""
        if self.daily_stats:
            self.daily_stats.trade_count += 1

    # ==================== 통합 체크 ====================

    def can_trade(self) -> tuple[bool, str]:
        """
        거래 가능 여부 종합 확인

        Returns:
            tuple[bool, str]: (거래 가능 여부, 불가 사유)
        """
        if self._is_trading_halted:
            return False, "거래 중단됨 (일일 손실 한도 초과)"

        if not self.check_daily_loss_limit():
            return False, "일일 최대 손실 한도 초과"

        if not self.check_daily_trade_limit():
            return False, "일일 최대 거래 횟수 초과"

        return True, ""

    def can_open_position(
        self,
        symbol: str,
        price: float,
        quantity: int,
        total_capital: float,
    ) -> tuple[bool, str]:
        """
        신규 포지션 진입 가능 여부

        Args:
            symbol: 종목코드
            price: 가격
            quantity: 수량
            total_capital: 총 자산

        Returns:
            tuple[bool, str]: (진입 가능 여부, 불가 사유)
        """
        # 기본 거래 가능 여부
        can, reason = self.can_trade()
        if not can:
            return False, reason

        amount = price * quantity

        # 종목 비중 확인
        if not self.check_position_weight(symbol, amount, total_capital):
            return False, f"종목 비중 초과 (최대 {self.config.max_stock_weight}%)"

        # 총 투자 비중 확인
        if not self.check_total_exposure(amount, total_capital):
            return False, f"총 투자 비중 초과 (최대 {self.config.max_total_position}%)"

        return True, ""

    # ==================== 포지션 관리 ====================

    def add_position(self, position: PositionState) -> None:
        """포지션 추가"""
        self.positions[position.symbol] = position

    def remove_position(self, symbol: str) -> Optional[PositionState]:
        """포지션 제거"""
        return self.positions.pop(symbol, None)

    def update_position_price(self, symbol: str, current_price: float) -> None:
        """포지션 현재가 업데이트"""
        if symbol in self.positions:
            self.positions[symbol].current_price = current_price
            # 트레일링 스탑용 최고가 업데이트
            if current_price > self.positions[symbol].highest_price:
                self.positions[symbol].highest_price = current_price

    def get_position(self, symbol: str) -> Optional[PositionState]:
        """포지션 조회"""
        return self.positions.get(symbol)

    def get_all_positions(self) -> list[PositionState]:
        """모든 포지션 조회"""
        return list(self.positions.values())

    def get_positions_to_close(self) -> list[tuple[PositionState, str]]:
        """
        청산해야 할 포지션 목록 조회

        Returns:
            list[tuple[PositionState, str]]: (포지션, 청산 사유) 목록
        """
        to_close = []
        for position in self.positions.values():
            should_close, reason = self.should_close_position(position)
            if should_close:
                to_close.append((position, reason))
        return to_close
