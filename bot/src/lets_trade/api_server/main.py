"""API 서버 메인 모듈"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .. import __version__
from .schemas.common import ErrorResponse, ErrorCode
from .routers import (
    system_router,
    account_router,
    portfolio_router,
    trades_router,
    signals_router,
    strategies_router,
    stocks_router,
    orders_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """앱 라이프사이클 관리"""
    # 시작 시 초기화
    yield
    # 종료 시 정리


def create_app() -> FastAPI:
    """FastAPI 앱 생성"""
    app = FastAPI(
        title="letsTrade API",
        description="LS증권 API 기반 주식 자동매매 백엔드",
        version=__version__,
        lifespan=lifespan,
    )

    # CORS 설정
    origins = [
        "http://localhost:3000",  # 로컬 Dashboard
        "https://letstrade.vercel.app",  # 프로덕션 Dashboard
    ]

    # 환경변수에서 추가 origin
    extra_origin = os.getenv("DASHBOARD_URL")
    if extra_origin:
        origins.append(extra_origin)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["*"],
    )

    # 전역 예외 핸들러
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=str(exc),
                details={"path": str(request.url.path)},
            ).model_dump(mode="json"),
        )

    # 라우터 마운트
    app.include_router(system_router, prefix="/api/v1/system", tags=["System"])
    app.include_router(account_router, prefix="/api/v1/account", tags=["Account"])
    app.include_router(portfolio_router, prefix="/api/v1/portfolio", tags=["Portfolio"])
    app.include_router(trades_router, prefix="/api/v1/trades", tags=["Trades"])
    app.include_router(signals_router, prefix="/api/v1/signals", tags=["Signals"])
    app.include_router(strategies_router, prefix="/api/v1/strategies", tags=["Strategies"])
    app.include_router(stocks_router, prefix="/api/v1/stocks", tags=["Stocks"])
    app.include_router(orders_router, prefix="/api/v1/orders", tags=["Orders"])

    return app


# 앱 인스턴스
app = create_app()
