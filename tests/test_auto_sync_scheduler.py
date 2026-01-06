from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Connection, Platform, SyncRun
from app.workers.auto_sync_tasks import schedule_auto_syncs


def test_auto_sync_scheduler_creates_run(db: Session, default_org_id: int):
    connection = Connection(
        organization_id=default_org_id,
        platform=Platform.stub,
        name="Auto Sync",
        credentials_json={},
        auto_sync_enabled=True,
        auto_sync_every_minutes=60,
        auto_sync_window_days=3,
    )
    db.add(connection)
    db.commit()
    db.refresh(connection)

    now = datetime(2023, 1, 5, tzinfo=timezone.utc)
    scheduled = schedule_auto_syncs(db, now=now, enqueue=False)
    assert scheduled == 1

    runs = db.query(SyncRun).filter(SyncRun.connection_id == connection.id).all()
    assert len(runs) == 1

    scheduled_again = schedule_auto_syncs(db, now=now, enqueue=False)
    assert scheduled_again == 0

    runs_again = db.query(SyncRun).filter(SyncRun.connection_id == connection.id).all()
    assert len(runs_again) == 1
