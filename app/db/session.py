from collections.abc import Generator
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings

settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
_TEST_SESSION = None


def get_db() -> Generator:
    db = _TEST_SESSION or SessionLocal()
    try:
        yield db
    finally:
        if _TEST_SESSION is None:
            db.close()


def get_session():
    return _TEST_SESSION or SessionLocal()


def is_test_session(session) -> bool:
    return session is _TEST_SESSION


def set_test_session(session) -> None:
    global _TEST_SESSION
    _TEST_SESSION = session


def clear_test_session() -> None:
    global _TEST_SESSION
    _TEST_SESSION = None
