"""전략 관련 라우터"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from ..dependencies import get_db, get_supabase_client
from ..schemas.strategy import (
    StrategySchema,
    StrategyListResponse,
    StrategyCreateRequest,
    StrategyUpdateRequest,
    StrategyToggleResponse,
)
from ..schemas.common import ErrorCode
from ...models import Strategy
from ...db.repository import BaseRepository

router = APIRouter()


@router.get("", response_model=StrategyListResponse)
async def get_strategies(
    limit: int = Query(default=50, le=100),
    offset: int = Query(default=0, ge=0),
    is_active: Optional[bool] = Query(default=None),
    strategy_type: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    """전략 목록 조회"""
    query = db.query(Strategy)

    # 필터링
    if is_active is not None:
        query = query.filter(Strategy.is_active == is_active)
    if strategy_type:
        query = query.filter(Strategy.strategy_type == strategy_type)

    # 정렬 (우선순위 → 생성일)
    query = query.order_by(Strategy.priority.desc(), Strategy.created_at.desc())

    total = query.count()
    active_count = db.query(Strategy).filter(Strategy.is_active == True).count()
    items = query.offset(offset).limit(limit).all()

    return StrategyListResponse(
        items=[StrategySchema.model_validate(item) for item in items],
        total=total,
        active_count=active_count,
        limit=limit,
        offset=offset,
    )


@router.get("/{strategy_id}", response_model=StrategySchema)
async def get_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """전략 상세 조회"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

    if not strategy:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.RESOURCE_NOT_FOUND,
                "message": f"전략 ID {strategy_id}를 찾을 수 없습니다.",
            },
        )

    return StrategySchema.model_validate(strategy)


@router.post("", response_model=StrategySchema)
async def create_strategy(
    request: StrategyCreateRequest,
    db: Session = Depends(get_db),
):
    """전략 생성"""
    try:
        strategy = Strategy(
            name=request.name,
            description=request.description,
            strategy_type=request.strategy_type,
            stock_codes=request.stock_codes,
            parameters=request.parameters,
            max_investment=request.max_investment,
            max_loss_rate=request.max_loss_rate,
            take_profit_rate=request.take_profit_rate,
            is_active=request.is_active,
            priority=request.priority,
        )

        db.add(strategy)
        db.commit()
        db.refresh(strategy)

        # Supabase 동기화
        try:
            supabase = get_supabase_client()
            repo = BaseRepository(Strategy, db, supabase, "strategies")
            repo.sync_to_remote(strategy)
        except Exception:
            pass  # Supabase 동기화 실패는 무시

        return StrategySchema.model_validate(strategy)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": ErrorCode.DATABASE_ERROR,
                "message": f"전략 생성 실패: {str(e)}",
            },
        )


@router.put("/{strategy_id}", response_model=StrategySchema)
async def update_strategy(
    strategy_id: int,
    request: StrategyUpdateRequest,
    db: Session = Depends(get_db),
):
    """전략 수정"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

    if not strategy:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.RESOURCE_NOT_FOUND,
                "message": f"전략 ID {strategy_id}를 찾을 수 없습니다.",
            },
        )

    try:
        # None이 아닌 필드만 업데이트
        update_data = request.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(strategy, key, value)

        db.commit()
        db.refresh(strategy)

        # Supabase 동기화
        try:
            supabase = get_supabase_client()
            repo = BaseRepository(Strategy, db, supabase, "strategies")
            repo.sync_to_remote(strategy)
        except Exception:
            pass

        return StrategySchema.model_validate(strategy)

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": ErrorCode.DATABASE_ERROR,
                "message": f"전략 수정 실패: {str(e)}",
            },
        )


@router.patch("/{strategy_id}/toggle", response_model=StrategyToggleResponse)
async def toggle_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """전략 활성화/비활성화 토글"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

    if not strategy:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.RESOURCE_NOT_FOUND,
                "message": f"전략 ID {strategy_id}를 찾을 수 없습니다.",
            },
        )

    try:
        strategy.is_active = not strategy.is_active
        db.commit()
        db.refresh(strategy)

        # Supabase 동기화
        try:
            supabase = get_supabase_client()
            repo = BaseRepository(Strategy, db, supabase, "strategies")
            repo.sync_to_remote(strategy)
        except Exception:
            pass

        return StrategyToggleResponse(
            id=strategy.id,
            is_active=strategy.is_active,
            updated_at=strategy.updated_at,
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": ErrorCode.DATABASE_ERROR,
                "message": f"전략 토글 실패: {str(e)}",
            },
        )


@router.delete("/{strategy_id}")
async def delete_strategy(strategy_id: int, db: Session = Depends(get_db)):
    """전략 삭제"""
    strategy = db.query(Strategy).filter(Strategy.id == strategy_id).first()

    if not strategy:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": ErrorCode.RESOURCE_NOT_FOUND,
                "message": f"전략 ID {strategy_id}를 찾을 수 없습니다.",
            },
        )

    try:
        db.delete(strategy)
        db.commit()

        # Supabase에서도 삭제
        try:
            supabase = get_supabase_client()
            supabase.table("strategies").delete().eq("id", strategy_id).execute()
        except Exception:
            pass

        return {"success": True, "message": f"전략 ID {strategy_id}가 삭제되었습니다."}

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": ErrorCode.DATABASE_ERROR,
                "message": f"전략 삭제 실패: {str(e)}",
            },
        )
