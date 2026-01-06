import os
import pytest

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from fastapi.testclient import TestClient

from app.main import create_app
from app.core.config import get_settings
from app.db.session import get_db
from app.db.base import Base
from app.db.models import Advertiser
from app.db import session as db_session_module


@pytest.fixture(scope="session")
def database_url() -> str:
    # read from env var matching Settings.database_url (DATABASE_URL), fallback to compose default
    return os.getenv("DATABASE_URL") or os.getenv("DATABASE_URL", "postgresql+psycopg2://postgres:postgres@db:5432/ads")


@pytest.fixture(scope="session")
def engine(database_url):
    engine = create_engine(database_url)
    return engine


@pytest.fixture()
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
    db_session_module.set_test_session(session)

    # restart SAVEPOINT after commit inside tested code
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(sess, transaction):
        if transaction.nested and not sess.in_nested_transaction():
            sess.begin_nested()

    try:
        yield session
    finally:
        db_session_module.clear_test_session()
        session.rollback()
        session.close()


@pytest.fixture(autouse=True)
def seed_default_advertiser(db_session):
    existing = db_session.query(Advertiser).filter(Advertiser.id == 1).first()
    if not existing:
        db_session.add(Advertiser(id=1, name="Default Advertiser"))
        db_session.commit()
        db_session.execute(text("SELECT setval('advertisers_id_seq', (SELECT max(id) FROM advertisers))"))
        db_session.commit()
    yield


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
