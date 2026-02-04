"""의존성 주입 (Dependency Injection)"""

from functools import lru_cache
from typing import Generator

from sqlalchemy.orm import Session
from supabase import Client

from ..api import LSApiClient, AccountApi, StockApi, OrderApi
from ..db.connection import db, get_sqlite_session, get_supabase


@lru_cache()
def get_ls_client() -> LSApiClient:
    """LS API 클라이언트 싱글톤"""
    return LSApiClient()


def get_account_api() -> AccountApi:
    """Account API 의존성"""
    return AccountApi(get_ls_client())


def get_stock_api() -> StockApi:
    """Stock API 의존성"""
    return StockApi(get_ls_client())


def get_order_api() -> OrderApi:
    """Order API 의존성"""
    return OrderApi(get_ls_client())


def get_db() -> Generator[Session, None, None]:
    """SQLite 세션 의존성"""
    yield from get_sqlite_session()


def get_supabase_client() -> Client:
    """Supabase 클라이언트 의존성"""
    return get_supabase()
