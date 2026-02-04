"""LS증권 API 설정"""

import os
from dataclasses import dataclass
from enum import Enum


class Environment(Enum):
    """API 환경 (모의투자/실전투자)"""
    SIMULATION = "simulation"  # 모의투자
    PRODUCTION = "production"  # 실전투자


@dataclass
class LSApiConfig:
    """LS증권 API 설정"""
    app_key: str
    app_secret: str
    account_no: str
    environment: Environment = Environment.SIMULATION

    @property
    def base_url(self) -> str:
        """환경에 따른 API Base URL"""
        if self.environment == Environment.PRODUCTION:
            return "https://openapi.ls-sec.co.kr:9443"
        return "https://openapi.ls-sec.co.kr:29443"

    @classmethod
    def from_env(cls) -> "LSApiConfig":
        """환경 변수에서 설정 로드"""
        app_key = os.getenv("LS_APP_KEY")
        app_secret = os.getenv("LS_APP_SECRET")
        account_no = os.getenv("LS_ACCOUNT_NO", "")
        api_url = os.getenv("LS_API_URL", "")

        if not app_key or not app_secret:
            raise ValueError("LS_APP_KEY와 LS_APP_SECRET 환경 변수가 필요합니다.")

        # URL로 환경 판단
        env = Environment.PRODUCTION if "9443" in api_url and "29443" not in api_url else Environment.SIMULATION

        return cls(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            environment=env,
        )
