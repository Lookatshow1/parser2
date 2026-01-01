from app.db.session import SessionLocal
from app.services.experiment_service import ExperimentService
from app.workers.celery_app import celery_app


@celery_app.task(bind=True)
def close_round_task(self, experiment_id: int) -> dict:
    session = SessionLocal()
    service = ExperimentService()
    try:
        round_item = service.close_round(session, experiment_id)
        if round_item is None:
            return {"round_index": None}
        return {"round_index": round_item.round_index}
    finally:
        session.close()
