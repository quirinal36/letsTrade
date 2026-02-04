"""포트폴리오 관련 라우터"""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import User, get_current_user
from ..dependencies import get_db, get_supabase_client, get_account_api
from ..schemas.portfolio import (
    PortfolioPositionSchema,
    PortfolioListResponse,
    PortfolioSummaryResponse,
    SyncResultResponse,
)
from ..schemas.common import ErrorCode
from ...models import Portfolio, Trade
from ...db.repository import BaseRepository

router = APIRouter()


@router.get("", response_model=PortfolioListResponse)
async def get_portfolio(
    current_user: User = Depends(get_current_user),
    limit: int = Query(default=100, le=500),
    offset: int = Query(default=0, ge=0),
    order_by: str = Query(default="market_value"),
    ascending: bool = Query(default=False),
    db: Session = Depends(get_db),
):
    """포트폴리오 목록 조회"""
    query = db.query(Portfolio)

    # 정렬
    order_column = getattr(Portfolio, order_by, Portfolio.market_value)
    if ascending:
        query = query.order_by(order_column.asc())
    else:
        query = query.order_by(order_column.desc())

    total = query.count()
    items = query.offset(offset).limit(limit).all()

    return PortfolioListResponse(
        items=[PortfolioPositionSchema.model_validate(item) for item in items],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/summary", response_model=PortfolioSummaryResponse)
async def get_portfolio_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """포트폴리오 요약 조회"""
    # 집계 쿼리
    result = db.query(
        func.sum(Portfolio.market_value).label("total_value"),
        func.sum(Portfolio.total_cost).label("total_cost"),
        func.sum(Portfolio.profit_loss).label("total_profit"),
        func.count(Portfolio.id).label("position_count"),
    ).first()

    total_value = result.total_value or Decimal(0)
    total_cost = result.total_cost or Decimal(0)
    total_profit = result.total_profit or Decimal(0)

    # 수익률 계산
    profit_rate = Decimal(0)
    if total_cost > 0:
        profit_rate = (total_profit / total_cost) * 100

    # 오늘 거래 수
    today = datetime.now().date()
    today_trade_count = (
        db.query(func.count(Trade.id))
        .filter(func.date(Trade.created_at) == today)
        .scalar()
        or 0
    )

    return PortfolioSummaryResponse(
        total_value=total_value,
        total_cost=total_cost,
        total_profit=total_profit,
        profit_rate=profit_rate,
        position_count=result.position_count or 0,
        today_trade_count=today_trade_count,
        timestamp=datetime.now(),
    )


@router.post("/sync", response_model=SyncResultResponse)
async def sync_portfolio(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """포트폴리오 동기화 (브로커 → DB → Supabase)"""
    try:
        account_api = get_account_api()
        supabase = get_supabase_client()

        # 브로커에서 보유 종목 조회
        positions = account_api.get_positions()

        added = 0
        updated = 0
        removed = 0

        # 현재 DB의 종목 코드 목록
        existing_codes = {p.stock_code for p in db.query(Portfolio.stock_code).all()}
        broker_codes = {p.symbol for p in positions}

        # 삭제할 종목 (DB에는 있지만 브로커에는 없음)
        to_remove = existing_codes - broker_codes
        if to_remove:
            db.query(Portfolio).filter(Portfolio.stock_code.in_(to_remove)).delete(
                synchronize_session=False
            )
            removed = len(to_remove)

        # 추가/업데이트
        for pos in positions:
            existing = (
                db.query(Portfolio).filter(Portfolio.stock_code == pos.symbol).first()
            )

            if existing:
                # 업데이트
                existing.stock_name = pos.name
                existing.quantity = pos.quantity
                existing.avg_price = Decimal(str(pos.avg_price))
                existing.current_price = Decimal(str(pos.current_price))
                existing.total_cost = Decimal(str(pos.total_cost))
                existing.market_value = Decimal(str(pos.market_value))
                existing.profit_loss = Decimal(str(pos.profit_loss))
                existing.profit_loss_rate = Decimal(str(pos.profit_rate))
                updated += 1
            else:
                # 새로 추가
                new_portfolio = Portfolio(
                    stock_code=pos.symbol,
                    stock_name=pos.name,
                    quantity=pos.quantity,
                    avg_price=Decimal(str(pos.avg_price)),
                    current_price=Decimal(str(pos.current_price)),
                    total_cost=Decimal(str(pos.total_cost)),
                    market_value=Decimal(str(pos.market_value)),
                    profit_loss=Decimal(str(pos.profit_loss)),
                    profit_loss_rate=Decimal(str(pos.profit_rate)),
                )
                db.add(new_portfolio)
                added += 1

        db.commit()

        # Supabase 동기화
        repo = BaseRepository(Portfolio, db, supabase, "portfolio")
        for item in db.query(Portfolio).all():
            repo.sync_to_remote(item)

        return SyncResultResponse(
            synced_count=added + updated,
            added=added,
            updated=updated,
            removed=removed,
            timestamp=datetime.now(),
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": ErrorCode.DATABASE_ERROR,
                "message": f"동기화 오류: {str(e)}",
            },
        )
