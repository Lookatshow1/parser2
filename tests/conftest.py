import os
import pytest

os.environ.setdefault(
    "CREDENTIALS_ENC_KEYS",
    "test:MDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA=",
)
os.environ.setdefault("CREDENTIALS_ENC_ACTIVE_KID", "test")
os.environ.setdefault("REDIS_URL", "redis://redis:6379/0")

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.engine import Engine

from fastapi.testclient import TestClient

from app.main import create_app
from app.core.config import get_settings
from app.db.session import get_db
from app.db.base import Base
from datetime import date as dt_date

from app.db.models import (
    Advertiser,
    Connection,
    Experiment,
    ExperimentStatus,
    Membership,
    MembershipRole,
    MetricSnapshot,
    Organization,
    Platform,
    User,
)
from app.services.auth_service import create_access_token, get_password_hash
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
def session(db_session):
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


@pytest.fixture()
def org_a(db_session):
    org = Organization(name="Org A")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture()
def org_b(db_session):
    org = Organization(name="Org B")
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)
    return org


@pytest.fixture()
def user_a(db_session, org_a):
    user = User(
        email="user_a@example.com",
        password_hash=get_password_hash("password123"),
        is_active=True,
        active_organization_id=org_a.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    db_session.add(Membership(user_id=user.id, organization_id=org_a.id, role=MembershipRole.owner.value))
    db_session.commit()
    return user


@pytest.fixture()
def user_b(db_session, org_b):
    user = User(
        email="user_b@example.com",
        password_hash=get_password_hash("password123"),
        is_active=True,
        active_organization_id=org_b.id,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    db_session.add(Membership(user_id=user.id, organization_id=org_b.id, role=MembershipRole.owner.value))
    db_session.commit()
    return user


@pytest.fixture()
def auth_context(user_a, org_a):
    token = create_access_token(str(user_a.id))["access_token"]
    headers = {
        "Authorization": f"Bearer {token}",
        "X-Org-Id": str(org_a.id),
    }
    return {"user": user_a, "org": org_a, "headers": headers}


@pytest.fixture()
def auth_headers(auth_context):
    return auth_context["headers"]


@pytest.fixture()
def connection_yandex(db_session, org_a):
    conn = Connection(
        organization_id=org_a.id,
        advertiser_id=1,
        platform=Platform.yandex,
        name="Yandex Connection",
        credentials_json={"mock": True},
    )
    db_session.add(conn)
    db_session.commit()
    db_session.refresh(conn)
    return conn


@pytest.fixture()
def experiment_a(db_session, org_a):
    exp = Experiment(
        organization_id=org_a.id,
        status=ExperimentStatus.draft,
    )
    db_session.add(exp)
    db_session.commit()
    db_session.refresh(exp)
    return exp


@pytest.fixture()
def metric_snapshot_factory(db_session):
    def _factory(
        *,
        connection: Connection,
        date: dt_date | None = None,
        level: str | None = None,
        campaign_external_id: str = "c1",
        ad_group_external_id: str | None = None,
        ad_external_id: str | None = None,
        clicks: int = 0,
        impressions: int = 0,
        spend: int = 0,
        leads: int = 0,
        purchases: int = 0,
        revenue: int = 0,
    ):
        resolved_level = level
        if resolved_level is None:
            if ad_external_id is not None:
                resolved_level = "ad"
            elif ad_group_external_id is not None:
                resolved_level = "ad_group"
            else:
                resolved_level = "campaign"
        snapshot = MetricSnapshot(
            organization_id=connection.organization_id,
            connection_id=connection.id,
            platform=connection.platform,
            date=date or dt_date.today(),
            level=resolved_level,
            campaign_external_id=campaign_external_id,
            ad_group_external_id=ad_group_external_id,
            ad_external_id=ad_external_id,
            clicks=clicks,
            impressions=impressions,
            spend=spend,
            leads=leads,
            purchases=purchases,
            revenue=revenue,
        )
        db_session.add(snapshot)
        db_session.commit()
        db_session.refresh(snapshot)
        return snapshot

    return _factory
