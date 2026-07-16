"""Quản lý kết nối cơ sở dữ liệu bất đồng bộ (Async Database Session & Engine) với SQLAlchemy 2.0.

Cung cấp các hàm tạo engine, session factory và dependency `get_session` cho FastAPI.
"""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from hospital_ai.core.config import Settings, get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def create_engine(settings: Settings | None = None) -> AsyncEngine:
    """Tạo mới một AsyncEngine kết nối đến cơ sở dữ liệu dựa theo chuỗi cấu hình database_url."""
    active_settings = settings or get_settings()
    return create_async_engine(active_settings.database_url, pool_pre_ping=True)


def get_engine() -> AsyncEngine:
    """Lấy hoặc khởi tạo instance singleton của AsyncEngine."""
    global _engine
    if _engine is None:
        _engine = create_engine()
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Lấy hoặc khởi tạo instance singleton của session maker cho AsyncSession."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependency cung cấp AsyncSession cho các router FastAPI hoặc service, tự động đóng session khi xong."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session

