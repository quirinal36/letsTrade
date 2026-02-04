"""계좌 관련 라우터"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from ..auth import User, get_current_user
from ..dependencies import get_account_api
from ..schemas.account import BalanceResponse, PositionsListResponse, PositionSchema
from ..schemas.common import ErrorCode
from ...api import AccountApi

router = APIRouter()


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_user),
    account_api: AccountApi = Depends(get_account_api),
):
    """계좌 잔고 조회 (인증 필요)"""
    try:
        balance = account_api.get_balance()

        # 예수금 상세 정보 추가
        deposit_info = account_api.get_deposit()

        return BalanceResponse(
            deposit=balance.deposit,
            available=balance.available,
            total_eval=balance.total_eval,
            total_profit=balance.total_profit,
            profit_rate=balance.profit_rate,
            d1_deposit=deposit_info.get("d1_deposit"),
            d2_deposit=deposit_info.get("d2_deposit"),
            substitute=deposit_info.get("substitute"),
            timestamp=datetime.now(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "error_code": ErrorCode.BROKER_API_ERROR,
                "message": f"브로커 API 오류: {str(e)}",
            },
        )


@router.get("/positions", response_model=PositionsListResponse)
async def get_positions(
    current_user: User = Depends(get_current_user),
    account_api: AccountApi = Depends(get_account_api),
):
    """보유 종목 조회 (인증 필요)"""
    try:
        positions = account_api.get_positions()

        position_schemas = [
            PositionSchema(
                symbol=p.symbol,
                name=p.name,
                quantity=p.quantity,
                avg_price=p.avg_price,
                current_price=p.current_price,
                total_cost=p.total_cost,
                market_value=p.market_value,
                profit_loss=p.profit_loss,
                profit_rate=p.profit_rate,
            )
            for p in positions
        ]

        return PositionsListResponse(
            positions=position_schemas,
            count=len(position_schemas),
            timestamp=datetime.now(),
        )
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail={
                "error_code": ErrorCode.BROKER_API_ERROR,
                "message": f"브로커 API 오류: {str(e)}",
            },
        )
