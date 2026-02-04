"""주식 시세 관련 라우터"""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException

from ..dependencies import get_stock_api
from ..schemas.stock import (
    StockPriceResponse,
    OrderBookResponse,
    StockTradeResponse,
    StockTradeListResponse,
    MultiPriceRequest,
    MultiPriceResponse,
)
from ..schemas.common import ErrorCode
from ...api import StockApi

router = APIRouter()


@router.get("/{symbol}/price", response_model=StockPriceResponse)
async def get_stock_price(
    symbol: str,
    stock_api: StockApi = Depends(get_stock_api),
):
    """주식 현재가 조회"""
    try:
        price = stock_api.get_price(symbol)

        return StockPriceResponse(
            symbol=price.symbol,
            name=price.name,
            price=price.price,
            change=price.change,
            change_rate=price.change_rate,
            volume=price.volume,
            open_price=price.open_price,
            high_price=price.high_price,
            low_price=price.low_price,
            prev_close=price.prev_close,
            timestamp=price.timestamp,
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "error_code": ErrorCode.BROKER_API_ERROR,
                "message": f"시세 조회 실패: {str(e)}",
            },
        )


@router.get("/{symbol}/orderbook", response_model=OrderBookResponse)
async def get_orderbook(
    symbol: str,
    stock_api: StockApi = Depends(get_stock_api),
):
    """호가 정보 조회"""
    try:
        orderbook = stock_api.get_orderbook(symbol)

        return OrderBookResponse(
            symbol=orderbook.symbol,
            ask_prices=orderbook.ask_prices,
            ask_volumes=orderbook.ask_volumes,
            bid_prices=orderbook.bid_prices,
            bid_volumes=orderbook.bid_volumes,
            timestamp=orderbook.timestamp,
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "error_code": ErrorCode.BROKER_API_ERROR,
                "message": f"호가 조회 실패: {str(e)}",
            },
        )


@router.get("/{symbol}/trades", response_model=StockTradeListResponse)
async def get_stock_trades(
    symbol: str,
    count: int = Query(default=20, le=100),
    stock_api: StockApi = Depends(get_stock_api),
):
    """체결 내역 조회"""
    try:
        trades = stock_api.get_trades(symbol, count)

        return StockTradeListResponse(
            items=[
                StockTradeResponse(
                    symbol=t.symbol,
                    price=t.price,
                    volume=t.volume,
                    trade_type=t.trade_type,
                    time=t.time,
                )
                for t in trades
            ],
            count=len(trades),
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "error_code": ErrorCode.BROKER_API_ERROR,
                "message": f"체결 내역 조회 실패: {str(e)}",
            },
        )


@router.post("/prices", response_model=MultiPriceResponse)
async def get_multiple_prices(
    request: MultiPriceRequest,
    stock_api: StockApi = Depends(get_stock_api),
):
    """복수 종목 시세 조회"""
    if len(request.symbols) > 20:
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": ErrorCode.VALIDATION_ERROR,
                "message": "최대 20종목까지만 조회 가능합니다.",
            },
        )

    prices = {}
    errors = {}

    for symbol in request.symbols:
        try:
            price = stock_api.get_price(symbol)
            prices[symbol] = StockPriceResponse(
                symbol=price.symbol,
                name=price.name,
                price=price.price,
                change=price.change,
                change_rate=price.change_rate,
                volume=price.volume,
                open_price=price.open_price,
                high_price=price.high_price,
                low_price=price.low_price,
                prev_close=price.prev_close,
                timestamp=price.timestamp,
            )
        except Exception as e:
            errors[symbol] = str(e)

    return MultiPriceResponse(
        prices=prices,
        errors=errors,
        timestamp=datetime.now(),
    )
