from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from pathlib import Path

from app.db.session import get_db, engine
from app.api.schemas import HealthResponse, HealthzResponse
from app.core.config import get_settings
import redis

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health_check(db: Session = Depends(get_db)):
    # Check DB
    db_ok = True
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        db_ok = False

    # Check Migrations
    migrations_ok = True
    current_rev = None
    head_rev = None
    try:
        conn = db.connection()
        context = MigrationContext.configure(conn)
        current_rev = context.get_current_revision()

        alembic_ini = Path(__file__).resolve().parents[2] / "alembic.ini"
        script = ScriptDirectory.from_config(Config(str(alembic_ini)))
        head_rev = script.get_current_head()

        if current_rev != head_rev:
            migrations_ok = False
    except Exception:
        migrations_ok = False

    # Check Redis
    redis_ok = True
    try:
        settings = get_settings()
        r = redis.from_url(settings.redis_url)
        if not r.ping():
            redis_ok = False
    except Exception:
        redis_ok = False

    return {
        "status": "ok" if db_ok and migrations_ok and redis_ok else "degraded",
        "db": {"ok": db_ok},
        "migrations": {
            "ok": migrations_ok,
            "current": current_rev,
            "head": head_rev
        },
        "redis": {"ok": redis_ok}
    }

@router.get("/healthz", response_model=HealthzResponse)
def liveness_probe():
    return {"status": "ok", "db": "unknown"}

@router.get("/readyz")
def readiness_probe(db: Session = Depends(get_db)):
    # Check DB
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"База данных недоступна: {str(e)}"
        )

    # Check Redis
    try:
        settings = get_settings()
        r = redis.from_url(settings.redis_url)
        if not r.ping():
            raise Exception("Redis ping failed")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis недоступен: {str(e)}"
        )

    return {"status": "ok"}
