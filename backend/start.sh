#!/bin/bash

celery -A backend.worker.celery_app worker --loglevel=info -P gevent -c 5 &

celery -A backend.celery_beat.celery_app beat --loglevel=info &

gunicorn backend.main:app \
  -k uvicorn.workers.UvicornWorker \
  -c gunicorn.conf.py \
  --bind 0.0.0.0:$PORT