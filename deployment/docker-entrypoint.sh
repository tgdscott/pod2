#!/bin/bash
set -e

if [ "$1" = 'web' ]; then
    exec python run.py
elif [ "$1" = 'worker' ]; then
    exec celery -A src.api.app.celery worker --loglevel=info
else
    exec "$@"
fi