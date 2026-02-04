"""LS증권 API 인증 모듈"""

import time
from dataclasses import dataclass
from typing import Optional

import httpx

from .config import LSApiConfig


@dataclass
class TokenInfo:
    """액세스 토큰 정보"""
    access_token: str
    token_type: str
    expires_in: int  # 초 단위
    issued_at: float  # timestamp

    @property
    def is_expired(self) -> bool:
        """토큰 만료 여부 (만료 1분 전에 갱신)"""
        buffer_seconds = 60
        return time.time() >= (self.issued_at + self.expires_in - buffer_seconds)


class LSAuthClient:
    """LS증권 API 인증 클라이언트"""

    TOKEN_ENDPOINT = "/oauth2/token"

    def __init__(self, config: LSApiConfig):
        self.config = config
        self._token: Optional[TokenInfo] = None
        self._client = httpx.Client(
            base_url=config.base_url,
            timeout=30.0,
        )

    def _request_token(self) -> TokenInfo:
        """Access Token 발급 요청"""
        response = self._client.post(
            self.TOKEN_ENDPOINT,
            data={
                "grant_type": "client_credentials",
                "appkey": self.config.app_key,
                "appsecretkey": self.config.app_secret,
                "scope": "oob",
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        response.raise_for_status()
        data = response.json()

        if "access_token" not in data:
            error_msg = data.get("error_description", data.get("message", "Unknown error"))
            raise AuthenticationError(f"토큰 발급 실패: {error_msg}")

        return TokenInfo(
            access_token=data["access_token"],
            token_type=data.get("token_type", "Bearer"),
            expires_in=int(data.get("expires_in", 86400)),  # 기본 24시간
            issued_at=time.time(),
        )

    def get_token(self) -> str:
        """유효한 Access Token 반환 (필요시 자동 갱신)"""
        if self._token is None or self._token.is_expired:
            self._token = self._request_token()
        return self._token.access_token

    def refresh_token(self) -> str:
        """토큰 강제 갱신"""
        self._token = self._request_token()
        return self._token.access_token

    def revoke_token(self) -> bool:
        """토큰 폐기"""
        if self._token is None:
            return True

        try:
            response = self._client.post(
                "/oauth2/revoke",
                data={
                    "token": self._token.access_token,
                    "appkey": self.config.app_key,
                    "appsecretkey": self.config.app_secret,
                },
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                },
            )
            response.raise_for_status()
            self._token = None
            return True
        except httpx.HTTPError:
            return False

    @property
    def is_authenticated(self) -> bool:
        """인증 상태 확인"""
        return self._token is not None and not self._token.is_expired

    def close(self):
        """리소스 정리"""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class AuthenticationError(Exception):
    """인증 관련 예외"""
    pass
