"""시그널 관련 라우터"""

from datetime import datetime, date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..dependencies import get_db
from ..schemas.signal import SignalSchema, SignalListResponse, SignalStatsResponse
from ...models import Signal, Strategy
from ...models.signal import SignalType, SignalStatus

router = APIRouter()


@router.get("", response_model=SignalListResponse)
async def get_signals(
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    strategy_id: Optional[int] = Query(default=None),
    signal_type: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    stock_code: Optional[str] = Query(default=None),
    from_date: Optional[date] = Query(default=None),
    to_date: Optional[date] = Query(default=None),
    min_strength: Optional[float] = Query(default=None, ge=0, le=100),
    db: Session = Depends(get_db),
):
    """시그널 목록 조회"""
    query = db.query(Signal)

    # 필터링
    if strategy_id:
        query = query.filter(Signal.strategy_id == strategy_id)
    if signal_type:
        query = query.filter(Signal.signal_type == signal_type)
    if status:
        query = query.filter(Signal.status == status)
    if stock_code:
        query = query.filter(Signal.stock_code == stock_code)
    if from_date:
        query = query.filter(func.date(Signal.created_at) >= from_date)
    if to_date:
        query = query.filter(func.date(Signal.created_at) <= to_date)
    if min_strength is not None:
        query = query.filter(Signal.strength >= min_strength)

    # 정렬 (최신순)
    query = query.order_by(Signal.created_at.desc())

    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return SignalListResponse(
        items=[SignalSchema.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=list[SignalStatsResponse])
async def get_signal_stats(
    period_days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
):
    """전략별 시그널 통계"""
    from_date = datetime.now() - timedelta(days=period_days)

    # 전략별 통계 집계
    strategies = db.query(Strategy).all()
    stats = []

    for strategy in strategies:
        signals = (
            db.query(Signal)
            .filter(
                Signal.strategy_id == strategy.id,
                Signal.created_at >= from_date,
            )
            .all()
        )

        total = len(signals)
        if total == 0:
            continue

        executed = sum(1 for s in signals if s.status == SignalStatus.EXECUTED.value)
        buy = sum(1 for s in signals if s.signal_type == SignalType.BUY.value)
        sell = sum(1 for s in signals if s.signal_type == SignalType.SELL.value)
        avg_strength = sum(float(s.strength) for s in signals) / total
        avg_confidence = sum(float(s.confidence) for s in signals) / total

        stats.append(
            SignalStatsResponse(
                strategy_id=strategy.id,
                strategy_name=strategy.name,
                total_signals=total,
                executed_signals=executed,
                buy_signals=buy,
                sell_signals=sell,
                avg_strength=round(avg_strength, 2),
                avg_confidence=round(avg_confidence, 2),
                period_days=period_days,
            )
        )

    return stats
