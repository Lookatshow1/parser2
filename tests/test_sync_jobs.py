import os
import pytest
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.db.models import Connection, CampaignPlan, Experiment, ExperimentStatus, Platform, SyncRun, SyncRunStatus, SyncRunType
from app.workers.sync_tasks import execute_sync_run

def test_sync_creates_run_and_enqueues_task(client: TestClient, db: Session, default_org_id: int):
    # 1. Setup
    conn = Connection(
        organization_id=default_org_id,
        platform=Platform.yandex,
        name="Test Yandex",
        credentials_json={"token": "fake"},
    )
    db.add(conn)
    db.commit()

    plan = CampaignPlan(
        organization_id=default_org_id,
        name="Test Plan",
        platform=Platform.yandex,
        advertiser_id=1,
        connection_id=conn.id,
    )
    db.add(plan)
    db.commit()

    exp = Experiment(plan_id=plan.id, organization_id=default_org_id, status=ExperimentStatus.running)
    db.add(exp)
    db.commit()

    # 2. Call API
    payload = {
        "platform": "yandex",
        "run_type": "full",
        "date_from": "2023-01-01",
        "date_to": "2023-01-02"
    }
    resp = client.post(f"/api/experiments/{exp.id}/sync", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "queued"
    run_id = data["id"]

    # 3. Verify DB
    run = db.query(SyncRun).get(run_id)
    assert run is not None
    assert run.status == SyncRunStatus.queued

def test_sync_run_success_in_mock(db: Session, default_org_id: int):
    # 1. Setup
    conn = Connection(
        organization_id=default_org_id,
        platform=Platform.yandex,
        name="Test Yandex",
        credentials_json={"token": "fake"},
    )
    db.add(conn)
    db.commit()

    plan = CampaignPlan(
        organization_id=default_org_id,
        name="Test Plan",
        platform=Platform.yandex,
        advertiser_id=1,
        connection_id=conn.id,
    )
    db.add(plan)
    db.commit()

    exp = Experiment(plan_id=plan.id, organization_id=default_org_id, status=ExperimentStatus.running)
    db.add(exp)
    db.commit()

    run = SyncRun(
        organization_id=default_org_id,
        experiment_id=exp.id,
        platform=Platform.yandex,
        run_type=SyncRunType.full,
        status=SyncRunStatus.queued,
        params_json={"date_from": "2023-01-01", "date_to": "2023-01-02"}
    )
    db.add(run)
    db.commit()

    # 2. Execute Task (Synchronously)
    os.environ["YANDEX_DIRECT_MOCK"] = "1"
    execute_sync_run(run.id)

    # 3. Verify
    db.refresh(run)
    assert run.status == SyncRunStatus.success
    assert run.started_at is not None
    assert run.finished_at is not None
    assert run.error_text is None

def test_prevent_parallel_runs(db: Session, default_org_id: int):
    # This test is tricky to simulate with advisory locks in a single thread/transaction flow easily
    # without threading or multiprocessing, because advisory locks are session/transaction bound.
    # However, we can verify that the lock logic is called.
    # A true integration test would require two concurrent workers.
    # Here we will just verify that if we manually acquire lock, the task fails.

    # 1. Setup
    conn = Connection(
        organization_id=default_org_id,
        platform=Platform.yandex,
        name="Test Yandex",
        credentials_json={"token": "fake"},
    )
    db.add(conn)
    db.commit()

    plan = CampaignPlan(
        organization_id=default_org_id,
        name="Test Plan",
        platform=Platform.yandex,
        advertiser_id=1,
        connection_id=conn.id,
    )
    db.add(plan)
    db.commit()

    exp = Experiment(plan_id=plan.id, organization_id=default_org_id, status=ExperimentStatus.running)
    db.add(exp)
    db.commit()

    run = SyncRun(
        organization_id=default_org_id,
        experiment_id=exp.id,
        platform=Platform.yandex,
        run_type=SyncRunType.campaigns,
        status=SyncRunStatus.queued,
        params_json={}
    )
    db.add(run)
    db.commit()

    # 2. Acquire lock manually in main session
    from app.services.lock_service import get_sync_lock_key, acquire_advisory_lock
    key = get_sync_lock_key(exp.id, "yandex")

    # We need a separate session to hold the lock if we want to test conflict
    # But execute_sync_run creates its own session.
    # So if we hold lock here, execute_sync_run should fail.

    acquired = acquire_advisory_lock(db, key)
    assert acquired is True

    # 3. Run task
    # Since we are in the same process but different session (inside task),
    # and we used transaction level lock (pg_try_advisory_xact_lock),
    # the lock is held until `db` session commits or rolls back.
    # We haven't committed yet in this test function after acquiring lock?
    # Wait, acquire_advisory_lock executes a statement. If autocommit is off, it's in transaction.

    # execute_sync_run creates a NEW session.
    result = execute_sync_run(run.id)

    # 4. Verify failure
    assert result == "Lock failed"
    db.expire_all()
    run_refreshed = db.query(SyncRun).get(run.id)
    assert run_refreshed.status == SyncRunStatus.failed
    assert "Already running" in run_refreshed.error_text

    # Release lock (by commit/rollback)
    db.rollback()
