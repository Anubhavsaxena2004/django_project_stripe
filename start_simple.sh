#!/bin/bash
set -e

echo "Starting application..."

# Create media directory
mkdir -p /tmp/media
chmod 755 /tmp/media

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start the application
echo "Starting gunicorn..."
exec gunicorn stock_prediction_main.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --timeout 120 