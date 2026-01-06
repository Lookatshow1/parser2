import os
import pytest

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from fastapi.testclient import TestClient

from app.main import create_app
from app.core.config import get_settings
from app.db.session import get_db
from app.db.base import Base


@pytest.fixture(scope="session")
def database_url() -> str:
    # read from env var matching Settings.database_url (DATABASE_URL), fallback to compose default
    return os.getenv("DATABASE_URL") or os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/ads")


@pytest.fixture(scope="session")
def engine(database_url):
    engine = create_engine(database_url)
    return engine


@pytest.fixture(scope="session")
def connection(engine):
    conn = engine.connect()
    # begin a non-ORM transaction for test isolation
    trans = conn.begin()
    yield conn
    trans.rollback()
    conn.close()


@pytest.fixture()
def db_session(connection):
    # start a SAVEPOINT (nested transaction)
    SessionLocal = sessionmaker(bind=connection, autoflush=False, autocommit=False)
    session = SessionLocal()
    session.begin_nested()

    # restart SAVEPOINT after commit inside tested code
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, transaction):
        if transaction.nested and not session.is_active:
            session.begin_nested()

    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="session")
def default_org_id() -> int:
    return get_settings().default_organization_id


@pytest.fixture()
def db(db_session):
    return db_session


@pytest.fixture()
def client(db_session):
    app = create_app()

    def _get_test_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as client:
        yield client
