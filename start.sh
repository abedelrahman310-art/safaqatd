#!/usr/bin/env bash
set -o errexit

echo "Running migrations..."
python manage.py migrate

echo "Setting up groups..."
python setup_groups.py

echo "Starting server..."
gunicorn config.wsgi:application
