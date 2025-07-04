FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Create media directory for storing plot images
RUN mkdir -p /tmp/media && chmod 755 /tmp/media

RUN python manage.py collectstatic --noinput

# CMD ["gunicorn", "stock_prediction_main.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"] 

# Make startup script executable
RUN chmod +x start.sh

CMD ["./start.sh"]