"""계좌 정보 조회 API"""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional

from .client import LSApiClient


@dataclass
class Position:
    """보유 종목 정보"""
    symbol: str          # 종목코드
    name: str            # 종목명
    quantity: int        # 보유수량
    avg_price: float     # 평균매입가
    current_price: int   # 현재가
    total_cost: float    # 매입금액
    market_value: int    # 평가금액
    profit_loss: float   # 평가손익
    profit_rate: float   # 수익률(%)


@dataclass
class Balance:
    """계좌 잔고 정보"""
    deposit: int         # 예수금
    available: int       # 주문가능금액
    total_eval: int      # 총평가금액
    total_profit: float  # 총평가손익
    profit_rate: float   # 총수익률(%)
    positions: list[Position]  # 보유종목 리스트


class AccountApi:
    """계좌 정보 조회 API"""

    def __init__(self, client: LSApiClient):
        self.client = client

    def get_balance(self, account_no: Optional[str] = None) -> Balance:
        """
        계좌 잔고 조회 (CSPAQ12300)

        Args:
            account_no: 계좌번호 (미입력시 config의 계좌번호 사용)

        Returns:
            Balance: 잔고 정보
        """
        acct = account_no or self.client.account_no
        acct_prefix = acct[:8] if len(acct) >= 8 else acct
        acct_suffix = acct[8:10] if len(acct) >= 10 else "01"

        response = self.client.post(
            path="/stock/accno",
            tr_cd="CSPAQ12300",
            data={
                "CSPAQ12300InBlock1": {
                    "AcntNo": acct_prefix,
                    "InptPwd": "",  # 비밀번호 (필요시)
                    "AcntTpCode": acct_suffix,
                    "BalCreTp": "0",
                }
            },
        )

        # 요약 정보
        summary = response.get("CSPAQ12300OutBlock2", {})
        deposit = int(summary.get("DpsastAmt", 0))
        available = int(summary.get("MnyOrdAbleAmt", 0))
        total_eval = int(summary.get("BalEvalAmt", 0))
        total_profit = float(summary.get("PnlSumAmt", 0))
        profit_rate = float(summary.get("EvalPnlRat", 0))

        # 보유종목
        positions = []
        items = response.get("CSPAQ12300OutBlock3", [])
        if isinstance(items, dict):
            items = [items]

        for item in items:
            if not item.get("IsuNo"):
                continue
            positions.append(Position(
                symbol=item.get("IsuNo", "").replace("A", ""),
                name=item.get("IsuNm", ""),
                quantity=int(item.get("BalQty", 0)),
                avg_price=float(item.get("PchsPrc", 0)),
                current_price=int(item.get("NowPrc", 0)),
                total_cost=float(item.get("PchsAmt", 0)),
                market_value=int(item.get("BalEvalAmt", 0)),
                profit_loss=float(item.get("EvalPnl", 0)),
                profit_rate=float(item.get("EvalPnlRat", 0)),
            ))

        return Balance(
            deposit=deposit,
            available=available,
            total_eval=total_eval,
            total_profit=total_profit,
            profit_rate=profit_rate,
            positions=positions,
        )

    def get_deposit(self, account_no: Optional[str] = None) -> dict:
        """
        예수금 상세 조회 (CSPAQ22200)

        Args:
            account_no: 계좌번호

        Returns:
            dict: 예수금 상세 정보
        """
        acct = account_no or self.client.account_no
        acct_prefix = acct[:8] if len(acct) >= 8 else acct
        acct_suffix = acct[8:10] if len(acct) >= 10 else "01"

        response = self.client.post(
            path="/stock/accno",
            tr_cd="CSPAQ22200",
            data={
                "CSPAQ22200InBlock1": {
                    "AcntNo": acct_prefix,
                    "InptPwd": "",
                    "AcntTpCode": acct_suffix,
                }
            },
        )

        block = response.get("CSPAQ22200OutBlock2", {})

        return {
            "deposit": int(block.get("DpsastAmt", 0)),         # 예수금
            "d1_deposit": int(block.get("D1DpsastAmt", 0)),    # D+1 예수금
            "d2_deposit": int(block.get("D2DpsastAmt", 0)),    # D+2 예수금
            "order_available": int(block.get("MnyOrdAbleAmt", 0)),  # 주문가능금액
            "substitute": int(block.get("SubstAmt", 0)),       # 대용금액
        }

    def get_positions(self, account_no: Optional[str] = None) -> list[Position]:
        """
        보유 종목만 조회

        Args:
            account_no: 계좌번호

        Returns:
            list[Position]: 보유 종목 리스트
        """
        balance = self.get_balance(account_no)
        return balance.positions
