"""letsTrade - Railway 배포용 진입점"""

import os
import sys

# src 폴더를 모듈 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import uvicorn
from fastapi import FastAPI
from lets_trade import __version__

app = FastAPI(
    title="letsTrade",
    description="LS증권 API 기반 주식 자동매매 프로그램",
    version=__version__,
)


@app.get("/")
async def root():
    """헬스체크 및 기본 정보"""
    return {
        "name": "letsTrade",
        "version": __version__,
        "status": "running",
    }


@app.get("/health")
async def health():
    """헬스체크 엔드포인트"""
    return {"status": "healthy"}


# TODO: 추가 API 엔드포인트
# - /api/trades: 거래 내역
# - /api/portfolio: 포트폴리오 현황
# - /api/strategies: 전략 설정


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
