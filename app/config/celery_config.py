from celery import Celery

celery_app = Celery(
    'worker',
    broker='amqp://guest:guest@localhost:5672//',
    backend='rpc://'
)

celery_app.conf.update(
    task_routes={
        'app.tasks.celery_tasks.*': {'queue': 'default'},
    },
    imports=['app.tasks.celery_tasks']
)
