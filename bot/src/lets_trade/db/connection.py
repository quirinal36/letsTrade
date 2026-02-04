"""데이터베이스 연결 관리"""

import os
from pathlib import Path
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from supabase import create_client, Client

from ..models import Base


class DatabaseManager:
    """SQLite + Supabase 하이브리드 데이터베이스 관리자"""

    def __init__(self):
        self._sqlite_engine = None
        self._sqlite_session_factory = None
        self._supabase_client: Client | None = None

    # =============================================
    # SQLite (로컬 캐시)
    # =============================================
    def init_sqlite(self, db_path: str | None = None) -> None:
        """SQLite 초기화"""
        if db_path is None:
            # 기본 경로: 프로젝트 루트의 data 폴더
            data_dir = Path(__file__).parent.parent.parent.parent / "data"
            data_dir.mkdir(exist_ok=True)
            db_path = str(data_dir / "cache.db")

        self._sqlite_engine = create_engine(
            f"sqlite:///{db_path}",
            echo=os.getenv("LOG_LEVEL", "INFO") == "DEBUG",
        )
        self._sqlite_session_factory = sessionmaker(bind=self._sqlite_engine)

        # 테이블 생성
        Base.metadata.create_all(self._sqlite_engine)

    def get_sqlite_session(self) -> Generator[Session, None, None]:
        """SQLite 세션 제공 (컨텍스트 매니저)"""
        if self._sqlite_session_factory is None:
            self.init_sqlite()

        session = self._sqlite_session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    @property
    def sqlite_engine(self):
        """SQLite 엔진 반환"""
        if self._sqlite_engine is None:
            self.init_sqlite()
        return self._sqlite_engine

    # =============================================
    # Supabase (클라우드)
    # =============================================
    def init_supabase(self) -> None:
        """Supabase 클라이언트 초기화"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")

        self._supabase_client = create_client(url, key)

    @property
    def supabase(self) -> Client:
        """Supabase 클라이언트 반환"""
        if self._supabase_client is None:
            self.init_supabase()
        return self._supabase_client


# 싱글톤 인스턴스
db = DatabaseManager()


def get_sqlite_session() -> Generator[Session, None, None]:
    """SQLite 세션 의존성 (FastAPI용)"""
    yield from db.get_sqlite_session()


def get_supabase() -> Client:
    """Supabase 클라이언트 반환"""
    return db.supabase
