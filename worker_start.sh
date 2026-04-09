#!/usr/bin/env bash
set -e

echo ">>> Starting Celery worker + beat..."
exec celery -A celery_worker worker \
    --beat \
    --loglevel=info \
    --concurrency=2 \
    --max-tasks-per-child=100
