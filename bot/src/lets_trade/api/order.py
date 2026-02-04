"""주식 주문 API"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from .client import ApiError, LSApiClient


class OrderType(Enum):
    """주문 유형"""
    LIMIT = "00"        # 지정가
    MARKET = "03"       # 시장가
    CONDITIONAL = "05"  # 조건부지정가
    BEST_LIMIT = "06"   # 최유리지정가
    FIRST_LIMIT = "07"  # 최우선지정가
    PRE_MARKET = "61"   # 장전시간외
    POST_MARKET = "81"  # 장후시간외
    AFTER_HOURS = "82"  # 시간외단일가


class OrderSide(Enum):
    """주문 방향"""
    BUY = "2"   # 매수
    SELL = "1"  # 매도


@dataclass
class OrderRequest:
    """주문 요청"""
    symbol: str                          # 종목코드
    side: OrderSide                      # 매수/매도
    quantity: int                        # 수량
    price: int = 0                       # 가격 (시장가는 0)
    order_type: OrderType = OrderType.LIMIT  # 주문유형


@dataclass
class OrderResult:
    """주문 결과"""
    order_no: str        # 주문번호
    symbol: str          # 종목코드
    side: str            # 매수/매도
    quantity: int        # 주문수량
    price: int           # 주문가격
    order_time: str      # 주문시간
    status: str          # 상태


@dataclass
class OrderHistory:
    """주문 내역"""
    order_no: str        # 주문번호
    symbol: str          # 종목코드
    name: str            # 종목명
    side: str            # 매수/매도
    order_qty: int       # 주문수량
    exec_qty: int        # 체결수량
    order_price: int     # 주문가격
    exec_price: int      # 체결가격
    status: str          # 상태
    order_time: str      # 주문시간


class OrderApi:
    """주식 주문 API"""

    # 주문 금액 한도 (안전장치)
    MAX_ORDER_AMOUNT = 10_000_000  # 1천만원

    def __init__(self, client: LSApiClient, max_amount: int = MAX_ORDER_AMOUNT):
        self.client = client
        self.max_amount = max_amount

    def _validate_order(self, request: OrderRequest) -> None:
        """주문 유효성 검증"""
        if request.quantity <= 0:
            raise OrderValidationError("주문 수량은 1주 이상이어야 합니다.")

        if request.order_type == OrderType.LIMIT and request.price <= 0:
            raise OrderValidationError("지정가 주문은 가격이 필요합니다.")

        # 주문 금액 한도 검사
        order_amount = request.quantity * request.price
        if order_amount > self.max_amount:
            raise OrderValidationError(
                f"주문 금액({order_amount:,}원)이 한도({self.max_amount:,}원)를 초과합니다."
            )

    def buy(
        self,
        symbol: str,
        quantity: int,
        price: int = 0,
        order_type: OrderType = OrderType.LIMIT,
    ) -> OrderResult:
        """
        매수 주문 (CSPAT00601)

        Args:
            symbol: 종목코드
            quantity: 수량
            price: 가격 (시장가는 0)
            order_type: 주문유형

        Returns:
            OrderResult: 주문 결과
        """
        request = OrderRequest(
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=quantity,
            price=price,
            order_type=order_type,
        )
        return self._place_order(request)

    def sell(
        self,
        symbol: str,
        quantity: int,
        price: int = 0,
        order_type: OrderType = OrderType.LIMIT,
    ) -> OrderResult:
        """
        매도 주문 (CSPAT00701)

        Args:
            symbol: 종목코드
            quantity: 수량
            price: 가격 (시장가는 0)
            order_type: 주문유형

        Returns:
            OrderResult: 주문 결과
        """
        request = OrderRequest(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=quantity,
            price=price,
            order_type=order_type,
        )
        return self._place_order(request)

    def _place_order(self, request: OrderRequest) -> OrderResult:
        """주문 실행"""
        self._validate_order(request)

        acct = self.client.account_no
        acct_prefix = acct[:8] if len(acct) >= 8 else acct
        acct_suffix = acct[8:10] if len(acct) >= 10 else "01"

        # 매수/매도에 따라 TR 코드 선택
        if request.side == OrderSide.BUY:
            tr_cd = "CSPAT00601"
            block_name = "CSPAT00601InBlock1"
        else:
            tr_cd = "CSPAT00701"
            block_name = "CSPAT00701InBlock1"

        response = self.client.post(
            path="/stock/order",
            tr_cd=tr_cd,
            data={
                block_name: {
                    "AcntNo": acct_prefix,
                    "InptPwd": "",
                    "AcntTpCode": acct_suffix,
                    "IsuNo": f"A{request.symbol}",  # 종목코드 앞에 A 추가
                    "OrdQty": request.quantity,
                    "OrdPrc": request.price,
                    "BnsTpCode": request.side.value,
                    "OrdprcPtnCode": request.order_type.value,
                    "MgntrnCode": "000",
                    "LoanDt": "",
                    "OrdCndiTpCode": "0",
                }
            },
        )

        # 응답 처리
        out_block = response.get(f"{tr_cd}OutBlock1", {}) or response.get(f"{tr_cd}OutBlock2", {})

        return OrderResult(
            order_no=out_block.get("OrdNo", ""),
            symbol=request.symbol,
            side="매수" if request.side == OrderSide.BUY else "매도",
            quantity=request.quantity,
            price=request.price,
            order_time=out_block.get("OrdTime", ""),
            status="접수",
        )

    def modify(
        self,
        order_no: str,
        symbol: str,
        quantity: int,
        price: int,
    ) -> OrderResult:
        """
        주문 정정 (CSPAT00801)

        Args:
            order_no: 원주문번호
            symbol: 종목코드
            quantity: 정정수량
            price: 정정가격

        Returns:
            OrderResult: 정정 결과
        """
        acct = self.client.account_no
        acct_prefix = acct[:8] if len(acct) >= 8 else acct
        acct_suffix = acct[8:10] if len(acct) >= 10 else "01"

        response = self.client.post(
            path="/stock/order",
            tr_cd="CSPAT00801",
            data={
                "CSPAT00801InBlock1": {
                    "AcntNo": acct_prefix,
                    "InptPwd": "",
                    "AcntTpCode": acct_suffix,
                    "OrgOrdNo": order_no,
                    "IsuNo": f"A{symbol}",
                    "OrdQty": quantity,
                    "OrdprcPtnCode": "00",  # 지정가
                    "OrdCndiTpCode": "0",
                    "OrdPrc": price,
                }
            },
        )

        out_block = response.get("CSPAT00801OutBlock1", {}) or response.get("CSPAT00801OutBlock2", {})

        return OrderResult(
            order_no=out_block.get("OrdNo", ""),
            symbol=symbol,
            side="정정",
            quantity=quantity,
            price=price,
            order_time=out_block.get("OrdTime", ""),
            status="정정접수",
        )

    def cancel(self, order_no: str, symbol: str, quantity: int) -> OrderResult:
        """
        주문 취소 (CSPAT00901)

        Args:
            order_no: 원주문번호
            symbol: 종목코드
            quantity: 취소수량

        Returns:
            OrderResult: 취소 결과
        """
        acct = self.client.account_no
        acct_prefix = acct[:8] if len(acct) >= 8 else acct
        acct_suffix = acct[8:10] if len(acct) >= 10 else "01"

        response = self.client.post(
            path="/stock/order",
            tr_cd="CSPAT00901",
            data={
                "CSPAT00901InBlock1": {
                    "AcntNo": acct_prefix,
                    "InptPwd": "",
                    "AcntTpCode": acct_suffix,
                    "OrgOrdNo": order_no,
                    "IsuNo": f"A{symbol}",
                    "OrdQty": quantity,
                }
            },
        )

        out_block = response.get("CSPAT00901OutBlock1", {}) or response.get("CSPAT00901OutBlock2", {})

        return OrderResult(
            order_no=out_block.get("OrdNo", ""),
            symbol=symbol,
            side="취소",
            quantity=quantity,
            price=0,
            order_time=out_block.get("OrdTime", ""),
            status="취소접수",
        )

    def get_orders(self, date: Optional[str] = None) -> list[OrderHistory]:
        """
        당일 주문 내역 조회 (t0425)

        Args:
            date: 조회일자 (YYYYMMDD, 미입력시 당일)

        Returns:
            list[OrderHistory]: 주문 내역 리스트
        """
        if date is None:
            date = datetime.now().strftime("%Y%m%d")

        acct = self.client.account_no
        acct_prefix = acct[:8] if len(acct) >= 8 else acct
        acct_suffix = acct[8:10] if len(acct) >= 10 else "01"

        response = self.client.post(
            path="/stock/accno",
            tr_cd="t0425",
            data={
                "t0425InBlock": {
                    "accno": acct_prefix,
                    "passwd": "",
                    "expcode": "",
                    "chegession": "0",
                    "sortgb": "1",
                    "cts_ordno": "",
                }
            },
        )

        orders = []
        items = response.get("t0425OutBlock1", [])
        if isinstance(items, dict):
            items = [items]

        for item in items:
            side = "매수" if item.get("medession", "") == "2" else "매도"
            orders.append(OrderHistory(
                order_no=item.get("ordno", ""),
                symbol=item.get("expcode", ""),
                name=item.get("hname", ""),
                side=side,
                order_qty=int(item.get("qty", 0)),
                exec_qty=int(item.get("cheqty", 0)),
                order_price=int(item.get("price", 0)),
                exec_price=int(item.get("cheprice", 0)),
                status=item.get("ordermtd", ""),
                order_time=item.get("ordtime", ""),
            ))

        return orders


class OrderValidationError(Exception):
    """주문 유효성 검증 오류"""
    pass
