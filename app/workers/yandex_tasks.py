from datetime import date

from sqlalchemy.orm import Session

from app.connectors.yandex_direct import YandexDirectConnector
from app.db.session import SessionLocal
from app.workers.celery_app import celery_app


@celery_app.task(bind=True)
def sync_yandex_metrics(self, date_from: str, date_to: str) -> dict:
    connector = YandexDirectConnector()
    metrics = connector.fetch_metrics(date.fromisoformat(date_from), date.fromisoformat(date_to))
    session: Session = SessionLocal()
    try:
        session.add_all(metrics)
        session.commit()
    finally:
        session.close()
    return {"saved": len(metrics)}
