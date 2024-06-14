#!/bin/sh

if [ "$1" = "uvicorn" ]; then
    exec uvicorn app.main:app --host 0.0.0.0 --port 8000
elif [ "$1" = "celery" ]; then
    exec celery --app app.config.celery_config.celery_app worker --loglevel=info --pool=solo
fi

exec "$@"
