"""주문 관련 라우터"""

from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import User, get_current_user
from ..dependencies import get_order_api, get_db, get_supabase_client
from ..schemas.order import (
    BuyOrderRequest,
    SellOrderRequest,
    ModifyOrderRequest,
    CancelOrderRequest,
    OrderResultResponse,
    BrokerOrderSchema,
    BrokerOrderListResponse,
)
from ..schemas.common import ErrorCode
from ...api import OrderApi
from ...api.order import OrderType, OrderValidationError
from ...models import Trade
from ...models.trade import OrderType as TradeOrderType, OrderStatus
from ...db.repository import BaseRepository

router = APIRouter()


def _create_trade_record(
    db: Session,
    order_result,
    order_type: str,
    symbol: str,
    quantity: int,
    price: int,
    strategy_id: int = None,
    signal_id: int = None,
    notes: str = None,
) -> Trade:
    """거래 기록 생성"""
    trade = Trade(
        order_no=order_result.order_no,
        stock_code=symbol,
        stock_name="",  # TODO: 종목명 조회
        order_type=order_type,
        status=OrderStatus.PENDING.value,
        quantity=quantity,
        price=Decimal(str(price)),
        executed_quantity=0,
        strategy_id=strategy_id,
        signal_id=signal_id,
        notes=notes,
    )
    db.add(trade)
    db.commit()
    db.refresh(trade)

    # Supabase 동기화
    try:
        supabase = get_supabase_client()
        repo = BaseRepository(Trade, db, supabase, "trades")
        repo.sync_to_remote(trade)
    except Exception:
        pass

    return trade


@router.post("/buy", response_model=OrderResultResponse)
async def buy_order(
    request: BuyOrderRequest,
    current_user: User = Depends(get_current_user),
    order_api: OrderApi = Depends(get_order_api),
    db: Session = Depends(get_db),
):
    """매수 주문 (인증 필요)"""
    try:
        # 주문 유형 결정
        order_type = OrderType.MARKET if request.order_type == "market" else OrderType.LIMIT

        # 시장가 주문 시 가격 검증
        if order_type == OrderType.LIMIT and request.price <= 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": ErrorCode.INVALID_ORDER,
                    "message": "지정가 주문은 가격이 필요합니다.",
                },
            )

        result = order_api.buy(
            symbol=request.symbol,
            quantity=request.quantity,
            price=request.price,
            order_type=order_type,
        )

        # 거래 기록 생성
        trade = _create_trade_record(
            db=db,
            order_result=result,
            order_type=TradeOrderType.BUY.value,
            symbol=request.symbol,
            quantity=request.quantity,
            price=request.price,
            strategy_id=request.strategy_id,
            signal_id=request.signal_id,
            notes=request.notes,
        )

        return OrderResultResponse(
            order_no=result.order_no,
            symbol=result.symbol,
            side=result.side,
            quantity=result.quantity,
            price=result.price,
            order_time=result.order_time,
            status=result.status,
            trade_id=trade.id,
        )

    except OrderValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": ErrorCode.INVALID_ORDER,
                "message": str(e),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "error_code": ErrorCode.BROKER_API_ERROR,
                "message": f"주문 실패: {str(e)}",
            },
        )


@router.post("/sell", response_model=OrderResultResponse)
async def sell_order(
    request: SellOrderRequest,
    current_user: User = Depends(get_current_user),
    order_api: OrderApi = Depends(get_order_api),
    db: Session = Depends(get_db),
):
    """매도 주문 (인증 필요)"""
    try:
        order_type = OrderType.MARKET if request.order_type == "market" else OrderType.LIMIT

        if order_type == OrderType.LIMIT and request.price <= 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error_code": ErrorCode.INVALID_ORDER,
                    "message": "지정가 주문은 가격이 필요합니다.",
                },
            )

        result = order_api.sell(
            symbol=request.symbol,
            quantity=request.quantity,
            price=request.price,
            order_type=order_type,
        )

        # 거래 기록 생성
        trade = _create_trade_record(
            db=db,
            order_result=result,
            order_type=TradeOrderType.SELL.value,
            symbol=request.symbol,
            quantity=request.quantity,
            price=request.price,
            strategy_id=request.strategy_id,
            signal_id=request.signal_id,
            notes=request.notes,
        )

        return OrderResultResponse(
            order_no=result.order_no,
            symbol=result.symbol,
            side=result.side,
            quantity=result.quantity,
            price=result.price,
            order_time=result.order_time,
            status=result.status,
            trade_id=trade.id,
        )

    except OrderValidationError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": ErrorCode.INVALID_ORDER,
                "message": str(e),
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "error_code": ErrorCode.BROKER_API_ERROR,
                "message": f"주문 실패: {str(e)}",
            },
        )


@router.put("/{order_no}", response_model=OrderResultResponse)
async def modify_order(
    order_no: str,
    request: ModifyOrderRequest,
    current_user: User = Depends(get_current_user),
    order_api: OrderApi = Depends(get_order_api),
):
    """주문 정정 (인증 필요)"""
    try:
        result = order_api.modify(
            order_no=order_no,
            symbol=request.symbol,
            quantity=request.quantity,
            price=request.price,
        )

        return OrderResultResponse(
            order_no=result.order_no,
            symbol=result.symbol,
            side=result.side,
            quantity=result.quantity,
            price=result.price,
            order_time=result.order_time,
            status=result.status,
        )

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "error_code": ErrorCode.BROKER_API_ERROR,
                "message": f"주문 정정 실패: {str(e)}",
            },
        )


@router.delete("/{order_no}", response_model=OrderResultResponse)
async def cancel_order(
    order_no: str,
    request: CancelOrderRequest,
    current_user: User = Depends(get_current_user),
    order_api: OrderApi = Depends(get_order_api),
):
    """주문 취소 (인증 필요)"""
    try:
        result = order_api.cancel(
            order_no=order_no,
            symbol=request.symbol,
            quantity=request.quantity,
        )

        return OrderResultResponse(
            order_no=result.order_no,
            symbol=result.symbol,
            side=result.side,
            quantity=result.quantity,
            price=result.price,
            order_time=result.order_time,
            status=result.status,
        )

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "error_code": ErrorCode.BROKER_API_ERROR,
                "message": f"주문 취소 실패: {str(e)}",
            },
        )


@router.get("", response_model=BrokerOrderListResponse)
async def get_broker_orders(
    current_user: User = Depends(get_current_user),
    order_api: OrderApi = Depends(get_order_api),
):
    """오늘 브로커 주문 내역 조회 (인증 필요)"""
    try:
        orders = order_api.get_orders()

        return BrokerOrderListResponse(
            items=[
                BrokerOrderSchema(
                    order_no=o.order_no,
                    symbol=o.symbol,
                    name=o.name,
                    side=o.side,
                    order_qty=o.order_qty,
                    exec_qty=o.exec_qty,
                    order_price=o.order_price,
                    exec_price=o.exec_price,
                    status=o.status,
                    order_time=o.order_time,
                )
                for o in orders
            ],
            count=len(orders),
            timestamp=datetime.now(),
        )

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "error_code": ErrorCode.BROKER_API_ERROR,
                "message": f"주문 내역 조회 실패: {str(e)}",
            },
        )
