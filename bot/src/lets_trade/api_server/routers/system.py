"""시스템 관련 라우터"""

import time
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..dependencies import get_ls_client, get_db, get_supabase_client
from ... import __version__

router = APIRouter()

# 서버 시작 시간
_start_time = time.time()


class HealthResponse(BaseModel):
    """헬스체크 응답"""

    status: Literal["healthy", "degraded", "unhealthy"]
    version: str
    timestamp: datetime


class SystemStatusResponse(BaseModel):
    """시스템 상태 응답"""

    status: str
    version: str
    broker_connected: bool
    database_connected: bool
    supabase_connected: bool
    active_strategies: int
    pending_orders: int
    uptime_seconds: float
    timestamp: datetime


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """헬스체크 엔드포인트"""
    return HealthResponse(
        status="healthy",
        version=__version__,
        timestamp=datetime.now(),
    )


@router.get("/status", response_model=SystemStatusResponse)
async def system_status():
    """시스템 상세 상태"""
    # 브로커 연결 확인
    broker_connected = False
    try:
        client = get_ls_client()
        broker_connected = client.is_authenticated
    except Exception:
        pass

    # DB 연결 확인
    database_connected = False
    try:
        session = next(get_db())
        session.execute("SELECT 1")
        database_connected = True
    except Exception:
        pass

    # Supabase 연결 확인
    supabase_connected = False
    try:
        supabase = get_supabase_client()
        supabase.table("trades").select("id").limit(1).execute()
        supabase_connected = True
    except Exception:
        pass

    return SystemStatusResponse(
        status="running",
        version=__version__,
        broker_connected=broker_connected,
        database_connected=database_connected,
        supabase_connected=supabase_connected,
        active_strategies=0,  # TODO: 실제 활성 전략 수
        pending_orders=0,  # TODO: 실제 대기 주문 수
        uptime_seconds=time.time() - _start_time,
        timestamp=datetime.now(),
    )
