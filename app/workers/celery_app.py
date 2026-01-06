import os
from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "ads_workers",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)

celery_app.autodiscover_tasks(["app.workers"])
celery_app.conf.imports = (
    "app.workers.sync_tasks",
    "app.workers.erir_tasks",
    "app.workers.experiment_tasks",
    "app.workers.yandex_tasks",
    "app.workers.tasks",
)
celery_app.conf.task_routes = {
    "app.workers.sync_tasks.execute_sync_run": "main-queue"
}

if os.getenv("PYTEST_CURRENT_TEST"):
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
