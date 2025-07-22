# syntax=docker/dockerfile:1
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    libpq-dev \
    python3-venv \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose Flask port
EXPOSE 5000

# Default command (can be overridden)
# Development (default):
CMD ["python", "run.py"]

# For production, comment the above line and uncomment the following:
# CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.api.app:create_app()"]