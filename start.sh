#!/usr/bin/env bash
set -o errexit

echo "Setting up permission groups..."
python manage.py setup_groups

echo "Starting Gunicorn server..."
gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers ${WEB_CONCURRENCY:-3} --timeout 120 --log-file -
