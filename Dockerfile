# syntax = docker/dockerfile:1

ARG PYTHON_VERSION=3.12-slim
FROM python:${PYTHON_VERSION} as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

WORKDIR /app

# Install system dependencies including PDF rendering requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    libpango-1.0-0 \
    libharfbuzz0b \
    libpangoft2-1.0-0 \
    libffi-dev \
    fonts-liberation \
    fonts-noto-cjk \
    fonts-freefont-ttf \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run collectstatic during build
RUN python manage.py collectstatic --noinput || true

EXPOSE 8080

# Production startup entrypoint with migrations and gunicorn
CMD ["sh", "-c", "python manage.py migrate --noinput && python seed_pilot_simulation.py && gunicorn config.wsgi:application --bind 0.0.0.0:8080 --workers 2 --threads 4 --timeout 120"]
