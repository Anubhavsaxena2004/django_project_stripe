#!/bin/bash

# Create media directory if it doesn't exist
mkdir -p /tmp/media
chmod 755 /tmp/media

# Run database migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Start the application
exec gunicorn stock_prediction_main.wsgi:application --bind 0.0.0.0:8000 --workers 3