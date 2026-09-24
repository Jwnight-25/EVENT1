from collections.abc import Generator
from functools import lru_cache

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings


@lru_cache
def get_session_factory() -> sessionmaker[Session]:
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    try:
        factory = get_session_factory()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    with factory() as session:
        yield session
