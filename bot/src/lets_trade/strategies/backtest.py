"""백테스팅 프레임워크"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

import pandas as pd

from .base import Signal, SignalType, Strategy


@dataclass
class Trade:
    """백테스트 거래 기록"""
    entry_date: datetime
    exit_date: Optional[datetime]
    symbol: str
    side: str  # "long" or "short"
    entry_price: float
    exit_price: Optional[float]
    quantity: int
    profit_loss: float = 0.0
    profit_rate: float = 0.0
    holding_days: int = 0


@dataclass
class BacktestResult:
    """백테스트 결과"""
    strategy_name: str
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    total_return: float        # 총 수익률 (%)
    annual_return: float       # 연간 수익률 (%)
    max_drawdown: float        # 최대 낙폭 (%)
    sharpe_ratio: float        # 샤프 비율
    win_rate: float            # 승률 (%)
    total_trades: int          # 총 거래 수
    winning_trades: int        # 수익 거래 수
    losing_trades: int         # 손실 거래 수
    avg_profit: float          # 평균 수익
    avg_loss: float            # 평균 손실
    profit_factor: float       # 손익비
    trades: list[Trade] = field(default_factory=list)
    equity_curve: pd.Series = field(default_factory=pd.Series)


class Backtester:
    """
    백테스팅 엔진

    전략의 과거 성과를 시뮬레이션합니다.
    """

    def __init__(
        self,
        strategy: Strategy,
        initial_capital: float = 10_000_000,
        commission: float = 0.00015,  # 수수료율 (0.015%)
        slippage: float = 0.001,      # 슬리피지 (0.1%)
    ):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

        # 상태
        self.capital = initial_capital
        self.position: Optional[dict] = None
        self.trades: list[Trade] = []
        self.equity_history: list[float] = []

    def run(
        self,
        data: pd.DataFrame,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> BacktestResult:
        """
        백테스트 실행

        Args:
            data: OHLCV 데이터 (index: datetime)
            start_date: 시작일
            end_date: 종료일

        Returns:
            BacktestResult: 백테스트 결과
        """
        # 기간 필터링
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]

        if data.empty:
            raise ValueError("데이터가 비어있습니다.")

        # 초기화
        self.capital = self.initial_capital
        self.position = None
        self.trades = []
        self.equity_history = [self.initial_capital]

        # 전략 초기화
        self.strategy.initialize()

        # 시뮬레이션
        for i in range(len(data)):
            current_data = data.iloc[:i+1]
            current_price = data.iloc[i]["close"]
            current_date = data.index[i]

            # 시그널 생성
            signal = self.strategy.generate_signal(current_data)

            # 시그널 처리
            self._process_signal(signal, current_price, current_date)

            # 자산 기록
            equity = self._calculate_equity(current_price)
            self.equity_history.append(equity)

        # 마지막 포지션 청산
        if self.position:
            self._close_position(data.iloc[-1]["close"], data.index[-1])

        # 결과 계산
        return self._calculate_result(data)

    def _process_signal(
        self,
        signal: Signal,
        current_price: float,
        current_date: datetime,
    ) -> None:
        """시그널 처리"""
        if not self.strategy.validate_signal(signal):
            return

        if signal.is_buy and self.position is None:
            # 매수
            self._open_position(signal, current_price, current_date)

        elif signal.is_sell and self.position is not None:
            # 매도
            self._close_position(current_price, current_date)

    def _open_position(
        self,
        signal: Signal,
        price: float,
        date: datetime,
    ) -> None:
        """포지션 진입"""
        # 슬리피지 적용
        entry_price = price * (1 + self.slippage)

        # 수량 계산
        quantity = self.strategy.calculate_position_size(signal, self.capital)
        if quantity <= 0:
            return

        # 비용 계산
        cost = entry_price * quantity
        commission = cost * self.commission

        if cost + commission > self.capital:
            # 자금 부족시 수량 조정
            quantity = int(self.capital / (entry_price * (1 + self.commission)))
            if quantity <= 0:
                return
            cost = entry_price * quantity
            commission = cost * self.commission

        # 포지션 기록
        self.position = {
            "entry_date": date,
            "entry_price": entry_price,
            "quantity": quantity,
            "symbol": signal.symbol,
        }

        # 자본 차감
        self.capital -= (cost + commission)

    def _close_position(self, price: float, date: datetime) -> None:
        """포지션 청산"""
        if self.position is None:
            return

        # 슬리피지 적용
        exit_price = price * (1 - self.slippage)

        # 수익 계산
        proceeds = exit_price * self.position["quantity"]
        commission = proceeds * self.commission
        net_proceeds = proceeds - commission

        profit_loss = net_proceeds - (
            self.position["entry_price"] * self.position["quantity"]
        )
        profit_rate = (
            (exit_price - self.position["entry_price"])
            / self.position["entry_price"]
            * 100
        )

        # 거래 기록
        trade = Trade(
            entry_date=self.position["entry_date"],
            exit_date=date,
            symbol=self.position["symbol"],
            side="long",
            entry_price=self.position["entry_price"],
            exit_price=exit_price,
            quantity=self.position["quantity"],
            profit_loss=profit_loss,
            profit_rate=profit_rate,
            holding_days=(date - self.position["entry_date"]).days,
        )
        self.trades.append(trade)

        # 자본 증가
        self.capital += net_proceeds
        self.position = None

    def _calculate_equity(self, current_price: float) -> float:
        """현재 자산 가치 계산"""
        equity = self.capital
        if self.position:
            equity += current_price * self.position["quantity"]
        return equity

    def _calculate_result(self, data: pd.DataFrame) -> BacktestResult:
        """결과 계산"""
        equity_series = pd.Series(self.equity_history, index=list(data.index) + [data.index[-1]])

        # 기본 지표
        final_capital = self.equity_history[-1]
        total_return = (final_capital - self.initial_capital) / self.initial_capital * 100

        # 연간 수익률
        days = (data.index[-1] - data.index[0]).days
        years = days / 365 if days > 0 else 1
        annual_return = ((1 + total_return / 100) ** (1 / years) - 1) * 100 if years > 0 else 0

        # 최대 낙폭
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()

        # 승패 분석
        winning_trades = [t for t in self.trades if t.profit_loss > 0]
        losing_trades = [t for t in self.trades if t.profit_loss <= 0]

        win_rate = len(winning_trades) / len(self.trades) * 100 if self.trades else 0
        avg_profit = sum(t.profit_loss for t in winning_trades) / len(winning_trades) if winning_trades else 0
        avg_loss = sum(t.profit_loss for t in losing_trades) / len(losing_trades) if losing_trades else 0
        profit_factor = abs(sum(t.profit_loss for t in winning_trades) / sum(t.profit_loss for t in losing_trades)) if losing_trades and sum(t.profit_loss for t in losing_trades) != 0 else 0

        # 샤프 비율 (단순 계산)
        returns = equity_series.pct_change().dropna()
        sharpe_ratio = (returns.mean() / returns.std() * (252 ** 0.5)) if returns.std() > 0 else 0

        return BacktestResult(
            strategy_name=self.strategy.name,
            start_date=data.index[0],
            end_date=data.index[-1],
            initial_capital=self.initial_capital,
            final_capital=final_capital,
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            total_trades=len(self.trades),
            winning_trades=len(winning_trades),
            losing_trades=len(losing_trades),
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            trades=self.trades,
            equity_curve=equity_series,
        )
