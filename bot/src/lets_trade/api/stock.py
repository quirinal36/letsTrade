"""주식 시세 조회 API"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from .client import LSApiClient


@dataclass
class StockPrice:
    """주식 현재가 정보"""
    symbol: str          # 종목코드
    name: str            # 종목명
    price: int           # 현재가
    change: int          # 전일대비
    change_rate: float   # 등락률
    volume: int          # 거래량
    open_price: int      # 시가
    high_price: int      # 고가
    low_price: int       # 저가
    prev_close: int      # 전일종가
    timestamp: datetime  # 조회시간


@dataclass
class OrderBook:
    """호가 정보"""
    symbol: str
    ask_prices: list[int]    # 매도호가 (낮은순)
    ask_volumes: list[int]   # 매도잔량
    bid_prices: list[int]    # 매수호가 (높은순)
    bid_volumes: list[int]   # 매수잔량
    timestamp: datetime


@dataclass
class Trade:
    """체결 정보"""
    symbol: str
    price: int           # 체결가
    volume: int          # 체결수량
    trade_type: str      # 매수/매도
    time: str            # 체결시간


class StockApi:
    """주식 시세 조회 API"""

    def __init__(self, client: LSApiClient):
        self.client = client

    def get_price(self, symbol: str) -> StockPrice:
        """
        주식 현재가 조회 (t1102)

        Args:
            symbol: 종목코드 (예: "005930")

        Returns:
            StockPrice: 현재가 정보
        """
        response = self.client.post(
            path="/stock/market-data",
            tr_cd="t1102",
            data={
                "t1102InBlock": {
                    "shcode": symbol,
                }
            },
        )

        block = response.get("t1102OutBlock", {})

        return StockPrice(
            symbol=symbol,
            name=block.get("hname", ""),
            price=int(block.get("price", 0)),
            change=int(block.get("change", 0)),
            change_rate=float(block.get("diff", 0)),
            volume=int(block.get("volume", 0)),
            open_price=int(block.get("open", 0)),
            high_price=int(block.get("high", 0)),
            low_price=int(block.get("low", 0)),
            prev_close=int(block.get("jnilclose", 0)),
            timestamp=datetime.now(),
        )

    def get_orderbook(self, symbol: str) -> OrderBook:
        """
        주식 호가 조회 (t1101)

        Args:
            symbol: 종목코드

        Returns:
            OrderBook: 호가 정보
        """
        response = self.client.post(
            path="/stock/market-data",
            tr_cd="t1101",
            data={
                "t1101InBlock": {
                    "shcode": symbol,
                }
            },
        )

        block = response.get("t1101OutBlock", {})

        # 매도호가 (1~10)
        ask_prices = []
        ask_volumes = []
        for i in range(1, 11):
            ask_prices.append(int(block.get(f"offerho{i}", 0)))
            ask_volumes.append(int(block.get(f"offerrem{i}", 0)))

        # 매수호가 (1~10)
        bid_prices = []
        bid_volumes = []
        for i in range(1, 11):
            bid_prices.append(int(block.get(f"bidho{i}", 0)))
            bid_volumes.append(int(block.get(f"bidrem{i}", 0)))

        return OrderBook(
            symbol=symbol,
            ask_prices=ask_prices,
            ask_volumes=ask_volumes,
            bid_prices=bid_prices,
            bid_volumes=bid_volumes,
            timestamp=datetime.now(),
        )

    def get_trades(self, symbol: str, count: int = 20) -> list[Trade]:
        """
        주식 체결 내역 조회 (t1301)

        Args:
            symbol: 종목코드
            count: 조회 건수 (기본 20)

        Returns:
            list[Trade]: 체결 내역 리스트
        """
        response = self.client.post(
            path="/stock/market-data",
            tr_cd="t1301",
            data={
                "t1301InBlock": {
                    "shcode": symbol,
                    "cvolume": count,
                }
            },
        )

        trades = []
        blocks = response.get("t1301OutBlock1", [])

        for block in blocks:
            trade_type = "매수" if block.get("sign", "") == "2" else "매도"
            trades.append(Trade(
                symbol=symbol,
                price=int(block.get("price", 0)),
                volume=int(block.get("cvolume", 0)),
                trade_type=trade_type,
                time=block.get("chetime", ""),
            ))

        return trades

    def get_multiple_prices(self, symbols: list[str]) -> dict[str, StockPrice]:
        """
        여러 종목 현재가 일괄 조회

        Args:
            symbols: 종목코드 리스트

        Returns:
            dict[str, StockPrice]: 종목코드별 현재가 정보
        """
        result = {}
        for symbol in symbols:
            try:
                result[symbol] = self.get_price(symbol)
            except Exception:
                continue
        return result
