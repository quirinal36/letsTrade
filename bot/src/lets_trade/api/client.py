"""LS증권 API 클라이언트"""

from typing import Any, Optional

import httpx

from .auth import AuthenticationError, LSAuthClient
from .config import LSApiConfig


class LSApiClient:
    """LS증권 API 기본 클라이언트"""

    def __init__(self, config: Optional[LSApiConfig] = None):
        self.config = config or LSApiConfig.from_env()
        self._auth = LSAuthClient(self.config)
        self._client = httpx.Client(
            base_url=self.config.base_url,
            timeout=30.0,
        )

    def _get_headers(self, tr_cd: str, tr_cont: str = "N") -> dict[str, str]:
        """API 호출 공통 헤더"""
        return {
            "Content-Type": "application/json; charset=utf-8",
            "Authorization": f"Bearer {self._auth.get_token()}",
            "tr_cd": tr_cd,
            "tr_cont": tr_cont,
            "tr_cont_key": "",
            "mac_address": "",
        }

    def request(
        self,
        method: str,
        path: str,
        tr_cd: str,
        data: Optional[dict] = None,
        params: Optional[dict] = None,
        tr_cont: str = "N",
    ) -> dict[str, Any]:
        """API 요청 실행"""
        headers = self._get_headers(tr_cd, tr_cont)

        try:
            response = self._client.request(
                method=method,
                url=path,
                headers=headers,
                json=data,
                params=params,
            )
            response.raise_for_status()
            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                # 토큰 만료 시 갱신 후 재시도
                self._auth.refresh_token()
                headers = self._get_headers(tr_cd, tr_cont)
                response = self._client.request(
                    method=method,
                    url=path,
                    headers=headers,
                    json=data,
                    params=params,
                )
                response.raise_for_status()
                return response.json()
            raise ApiError(f"API 요청 실패: {e.response.status_code} - {e.response.text}")

        except httpx.RequestError as e:
            raise ApiError(f"네트워크 오류: {str(e)}")

    def get(
        self,
        path: str,
        tr_cd: str,
        params: Optional[dict] = None,
        tr_cont: str = "N",
    ) -> dict[str, Any]:
        """GET 요청"""
        return self.request("GET", path, tr_cd, params=params, tr_cont=tr_cont)

    def post(
        self,
        path: str,
        tr_cd: str,
        data: Optional[dict] = None,
        tr_cont: str = "N",
    ) -> dict[str, Any]:
        """POST 요청"""
        return self.request("POST", path, tr_cd, data=data, tr_cont=tr_cont)

    @property
    def is_authenticated(self) -> bool:
        """인증 상태 확인"""
        return self._auth.is_authenticated

    @property
    def account_no(self) -> str:
        """계좌번호"""
        return self.config.account_no

    def close(self):
        """리소스 정리"""
        self._auth.close()
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


class ApiError(Exception):
    """API 호출 관련 예외"""
    pass
