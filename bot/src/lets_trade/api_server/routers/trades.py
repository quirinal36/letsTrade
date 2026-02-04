"""거래 내역 라우터"""

from datetime import datetime, date
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func, and_
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..schemas.trade import TradeSchema, TradeListResponse, TradeSummary
from ..schemas.common import ErrorCode
from ...models import Trade
from ...models.trade import OrderStatus, OrderType

router = APIRouter()


@router.get("", response_model=TradeListResponse)
async def get_trades(
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None),
    order_type: Optional[str] = Query(default=None),
    stock_code: Optional[str] = Query(default=None),
    strategy_id: Optional[int] = Query(default=None),
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    db: Session = Depends(get_db),
):
    """거래 내역 조회"""
    query = db.query(Trade)

    # 필터링
    if status:
        query = query.filter(Trade.status == status)
    if order_type:
        query = query.filter(Trade.order_type == order_type)
    if stock_code:
        query = query.filter(Trade.stock_code == stock_code)
    if strategy_id:
        query = query.filter(Trade.strategy_id == strategy_id)
    if from_date:
        query = query.filter(func.date(Trade.created_at) >= from_date)
    if to_date:
        query = query.filter(func.date(Trade.created_at) <= to_date)

    # 정렬 (최신순)
    query = query.order_by(Trade.created_at.desc())

    total = query.count()
    items = query.offset(offset).limit(limit).all()

    # 요약 통계
    summary_query = db.query(Trade)
    if from_date:
        summary_query = summary_query.filter(func.date(Trade.created_at) >= from_date)
    if to_date:
        summary_query = summary_query.filter(func.date(Trade.created_at) <= to_date)

    total_count = summary_query.count()
    buy_count = summary_query.filter(Trade.order_type == OrderType.BUY.value).count()
    sell_count = summary_query.filter(Trade.order_type == OrderType.SELL.value).count()
    executed_count = summary_query.filter(
        Trade.status == OrderStatus.EXECUTED.value
    ).count()
    pending_count = summary_query.filter(
        Trade.status == OrderStatus.PENDING.value
    ).count()

    return TradeListResponse(
        items=[TradeSchema.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
        summary=TradeSummary(
            total_count=total_count,
            buy_count=buy_count,
            sell_count=sell_count,
            executed_count=executed_count,
            pending_count=pending_count,
        ),
    )


@router.get("/today", response_model=TradeListResponse)
async def get_today_trades(
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    """오늘 거래 내역 조회"""
    today = datetime.now().date()

    query = db.query(Trade).filter(func.date(Trade.created_at) == today)
    query = query.order_by(Trade.created_at.desc())

    total = query.count()
    items = query.offset(offset).limit(limit).all()

    # 오늘 요약
    buy_count = (
        db.query(Trade)
        .filter(
            and_(
                func.date(Trade.created_at) == today,
                Trade.order_type == OrderType.BUY.value,
            )
        )
        .count()
    )
    sell_count = (
        db.query(Trade)
        .filter(
            and_(
                func.date(Trade.created_at) == today,
                Trade.order_type == OrderType.SELL.value,
            )
        )
        .count()
    )
    executed_count = (
        db.query(Trade)
        .filter(
            and_(
                func.date(Trade.created_at) == today,
                Trade.status == OrderStatus.EXECUTED.value,
            )
        )
        .count()
    )
    pending_count = (
        db.query(Trade)
        .filter(
            and_(
                func.date(Trade.created_at) == today,
                Trade.status == OrderStatus.PENDING.value,
            )
        )
        .count()
    )

    return TradeListResponse(
        items=[TradeSchema.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
        summary=TradeSummary(
            total_count=total,
            buy_count=buy_count,
            sell_count=sell_count,
            executed_count=executed_count,
            pending_count=pending_count,
        ),
    )


@router.get("/{trade_id}", response_model=TradeSchema)
async def get_trade(trade_id: int, db: Session = Depends(get_db)):
    """거래 상세 조회"""
    trade = db.query(Trade).filter(Trade.id == trade_id).first()

    if not trade:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.RESOURCE_NOT_FOUND,
                "message": f"거래 ID {trade_id}를 찾을 수 없습니다.",
            },
        )

    return TradeSchema.model_validate(trade)
