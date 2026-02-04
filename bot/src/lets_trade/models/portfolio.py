"""포트폴리오 모델"""

from decimal import Decimal
from sqlalchemy import String, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class Portfolio(Base, TimestampMixin):
    """포트폴리오 (보유 종목) 테이블"""
    __tablename__ = "portfolio"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # 종목 정보
    stock_code: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    stock_name: Mapped[str] = mapped_column(String(100), nullable=False)

    # 보유 수량 및 금액
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    avg_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)  # 평균 매입가
    current_price: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)  # 현재가

    # 손익 정보 (계산용 캐시)
    total_cost: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)  # 총 매입금액
    market_value: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)  # 평가금액
    profit_loss: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False, default=0)  # 손익금액
    profit_loss_rate: Mapped[Decimal] = mapped_column(Numeric(8, 4), nullable=False, default=0)  # 손익률

    def __repr__(self) -> str:
        return f"<Portfolio {self.stock_code}: {self.quantity}주 @ {self.avg_price}>"

    def update_profit_loss(self) -> None:
        """손익 정보 업데이트"""
        self.market_value = Decimal(self.quantity) * self.current_price
        self.profit_loss = self.market_value - self.total_cost
        if self.total_cost > 0:
            self.profit_loss_rate = (self.profit_loss / self.total_cost) * 100
        else:
            self.profit_loss_rate = Decimal(0)
