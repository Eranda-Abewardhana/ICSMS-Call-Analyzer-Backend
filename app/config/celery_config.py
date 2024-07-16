import redis
from celery import Celery

from app.config.config import Configurations


celery_app = Celery(__name__, broker=Configurations.celery_broker_url, backend=Configurations.celery_result_backend)
redis_client = redis.Redis(host=Configurations.redis_host, port=Configurations.redis_port, db=0)


celery_app.conf.update(
    imports=['app.tasks.celery_tasks'],
    broker_connection_retry_on_startup=True,
    task_track_started=True
)
