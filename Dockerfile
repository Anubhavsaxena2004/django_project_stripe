FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Create media directory for storing plot images
RUN mkdir -p /tmp/media && chmod 755 /tmp/media

# Make startup scripts executable
RUN chmod +x start.sh start_simple.sh

# Use the simple startup script
CMD ["./start_simple.sh"]