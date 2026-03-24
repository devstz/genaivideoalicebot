from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config.settings import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=20,
    max_overflow=10,
    pool_timeout=10,
    pool_recycle=3600,
)

SessionFactory = async_sessionmaker( # type: ignore
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)
