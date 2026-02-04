"""데이터베이스 Repository 패턴"""

from typing import Generic, TypeVar, Type, List, Optional
from sqlalchemy.orm import Session
from supabase import Client

from ..models import Base

T = TypeVar("T", bound=Base)


class BaseRepository(Generic[T]):
    """기본 Repository (SQLite + Supabase 동기화)"""

    def __init__(
        self,
        model: Type[T],
        session: Session,
        supabase: Client,
        table_name: str,
    ):
        self.model = model
        self.session = session
        self.supabase = supabase
        self.table_name = table_name

    # =============================================
    # SQLite 로컬 작업
    # =============================================
    def get_local(self, id: int) -> Optional[T]:
        """로컬에서 ID로 조회"""
        return self.session.query(self.model).filter(self.model.id == id).first()

    def get_all_local(self, limit: int = 100, offset: int = 0) -> List[T]:
        """로컬에서 전체 조회"""
        return self.session.query(self.model).limit(limit).offset(offset).all()

    def create_local(self, obj: T) -> T:
        """로컬에 생성"""
        self.session.add(obj)
        self.session.flush()
        return obj

    def update_local(self, obj: T) -> T:
        """로컬에서 수정"""
        self.session.merge(obj)
        self.session.flush()
        return obj

    def delete_local(self, id: int) -> bool:
        """로컬에서 삭제"""
        obj = self.get_local(id)
        if obj:
            self.session.delete(obj)
            return True
        return False

    # =============================================
    # Supabase 클라우드 작업
    # =============================================
    def get_remote(self, id: int) -> Optional[dict]:
        """Supabase에서 ID로 조회"""
        result = self.supabase.table(self.table_name).select("*").eq("id", id).execute()
        return result.data[0] if result.data else None

    def get_all_remote(self, limit: int = 100, offset: int = 0) -> List[dict]:
        """Supabase에서 전체 조회"""
        result = (
            self.supabase.table(self.table_name)
            .select("*")
            .range(offset, offset + limit - 1)
            .execute()
        )
        return result.data

    def create_remote(self, data: dict) -> dict:
        """Supabase에 생성"""
        result = self.supabase.table(self.table_name).insert(data).execute()
        return result.data[0] if result.data else {}

    def update_remote(self, id: int, data: dict) -> dict:
        """Supabase에서 수정"""
        result = self.supabase.table(self.table_name).update(data).eq("id", id).execute()
        return result.data[0] if result.data else {}

    def delete_remote(self, id: int) -> bool:
        """Supabase에서 삭제"""
        result = self.supabase.table(self.table_name).delete().eq("id", id).execute()
        return len(result.data) > 0

    # =============================================
    # 동기화 작업
    # =============================================
    def sync_to_remote(self, obj: T) -> dict:
        """로컬 → Supabase 동기화"""
        data = {
            c.name: getattr(obj, c.name)
            for c in obj.__table__.columns
            if c.name != "id" or getattr(obj, "id") is not None
        }

        # datetime 직렬화
        for key, value in data.items():
            if hasattr(value, "isoformat"):
                data[key] = value.isoformat()
            elif hasattr(value, "__str__") and not isinstance(value, (str, int, float, bool, type(None))):
                data[key] = str(value)

        if obj.id:
            return self.update_remote(obj.id, data)
        else:
            return self.create_remote(data)

    def sync_from_remote(self, remote_data: dict) -> T:
        """Supabase → 로컬 동기화"""
        obj = self.model(**remote_data)
        return self.update_local(obj)
