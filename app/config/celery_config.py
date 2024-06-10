import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()


celery_app = Celery(__name__, broker=os.getenv("CELERY_BROKER_URL"), backend=os.getenv("CELERY_RESULT_BACKEND"))

celery_app.conf.update(
    imports=['app.tasks.celery_tasks'],
    broker_connection_retry_on_startup=True,
    task_track_started=True
)
