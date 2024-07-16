from celery import Celery

from app.config.config import Configurations


celery_app = Celery(__name__, broker=Configurations.celery_broker_url, backend=Configurations.celery_result_backend)

celery_app.conf.update(
    imports=['app.tasks.celery_tasks'],
    broker_connection_retry_on_startup=True,
    task_track_started=True
)
