"""letsTrade - Railway 배포용 진입점"""

import os
import sys

# src 폴더를 모듈 경로에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

import uvicorn
from lets_trade import __version__
from lets_trade.api_server import create_app

# API 서버 앱 생성
app = create_app()


# 기존 루트 엔드포인트 유지 (하위 호환성)
@app.get("/")
async def root():
    """헬스체크 및 기본 정보"""
    return {
        "name": "letsTrade",
        "version": __version__,
        "status": "running",
        "docs": "/docs",
        "api": "/api/v1",
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
