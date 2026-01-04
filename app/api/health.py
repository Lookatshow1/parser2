from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from alembic.config import Config
from alembic.script import ScriptDirectory

from app.api.schemas import HealthResponse, HealthDb, HealthMigrations
from app.db.session import get_db

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health_check(session: Session = Depends(get_db)):
    # 1. Check DB
    db_ok = False
    try:
        session.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    # 2. Check Migrations
    migrations_ok = False
    current_rev = None
    head_rev = None

    try:
        # Get current revision from DB
        result = session.execute(text("SELECT version_num FROM alembic_version"))
        row = result.first()
        if row:
            current_rev = row[0]
        else:
            current_rev = "missing"

        # Get head revision from Alembic config
        alembic_cfg = Config("alembic.ini")
        script = ScriptDirectory.from_config(alembic_cfg)
        head_rev = script.get_current_head()

        if current_rev and head_rev and current_rev == head_rev:
            migrations_ok = True

    except Exception:
        if not current_rev:
            current_rev = "error"
        if not head_rev:
            head_rev = "error"

    status = "ok" if db_ok and migrations_ok else "degraded"

    return HealthResponse(
        status=status,
        db=HealthDb(ok=db_ok),
        migrations=HealthMigrations(
            ok=migrations_ok,
            current=current_rev,
            head=head_rev
        )
    )
