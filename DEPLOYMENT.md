# Deployment Guide

## Current Status: Docker Infrastructure Complete, Celery Import Blocker

### What's Working
- **Docker Build**: Successfully builds with Python 3.11 and all dependencies
- **Flask Application**: Runs in Docker container on port 5000
- **Redis Service**: Running and accessible to other containers
- **Volume Mounts**: uploads/, outputs/, test_files/, database working correctly
- **Environment Variables**: .env file loading properly
- **Multi-Service Architecture**: Docker Compose orchestrates all services

### Current Blocker
- **Celery Worker**: Cannot import core.celery_worker module in Docker container
- **Error**: ModuleNotFoundError: No module named 'core.celery_worker'
- **Impact**: Background episode processing completely non-functional
- **Root Cause**: core/celery_worker.py file missing from Docker container

## Docker Setup

### Prerequisites
- Docker and Docker Compose installed
- Python 3.11 compatibility
- System dependencies: libpq-dev, ffmpeg, libsndfile1

### Configuration Files

#### docker-compose.yml
```yaml
version: '3.8'
services:
  redis:
    image: redis:7
    ports:
      - "6379:6379"
  
  web:
    build: .
    command: python run.py
    ports:
      - "5000:5000"
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
      - ./test_files:/app/test_files
      - ./podcastpro_dev.db:/app/podcastpro_dev.db
    env_file:
      - .env
    working_dir: /app/src
    environment:
      - PYTHONPATH=/app/src
    depends_on:
      - redis
  
  celery:
    build: .
    command: celery -A core.celery_worker.celery worker --loglevel=info
    working_dir: /app/src
    volumes:
      - ./uploads:/app/uploads
      - ./outputs:/app/outputs
      - ./test_files:/app/test_files
      - ./podcastpro_dev.db:/app/podcastpro_dev.db
    env_file:
      - .env
    environment:
      - PYTHONPATH=/app/src
    depends_on:
      - redis
```

#### Dockerfile
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    ffmpeg \
    libsndfile1 \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app/src
ENV PYTHONPATH=/app/src

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
CMD ["python", "run.py"]
```

#### .env
```env
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
```

## Deployment Steps

### 1. Build and Start Services
```bash
# Build the Docker image
docker-compose build

# Start all services
docker-compose up
```

### 2. Verify Services
- **Flask**: http://localhost:5000
- **Redis**: Running on port 6379
- **Celery**: Should start but currently fails due to import issue

### 3. Current Issues to Resolve

#### Critical: Celery Worker Import
- **Problem**: core/celery_worker.py missing from Docker container
- **Investigation Needed**: Check .dockerignore and build context
- **Fix Required**: Ensure file is copied to container during build

#### Background Processing
- **Status**: Non-functional due to Celery import issue
- **Impact**: Episode processing cannot complete
- **Dependencies**: Redis, Celery worker, task registration

## Troubleshooting

### Common Issues

#### Port Already Allocated
```bash
# Stop conflicting containers
docker ps
docker stop <container_id>
```

#### Redis Connection Issues
- Verify .env file contains correct Redis URLs
- Check Docker network connectivity
- Ensure Redis service is running

#### Celery Import Errors
- Verify core/celery_worker.py exists in source
- Check Docker build context
- Confirm PYTHONPATH and working directory settings

### Debugging Commands
```bash
# Check container contents
docker run -it --rm -w /app/src aaapodcastpro:latest ls -la

# Test imports in container
docker run -it --rm -w /app/src aaapodcastpro:latest python -c "import core.celery_worker"

# Check Celery worker startup
docker-compose logs celery
```

## Production Considerations

### Security
- Use production Redis with authentication
- Implement proper logging and monitoring
- Add health checks for all services

### Performance
- Configure Redis persistence
- Optimize Celery worker processes
- Add load balancing for web service

### Monitoring
- Add application metrics
- Monitor background job queue
- Set up error alerting

## Next Steps
1. Resolve Celery worker import issue
2. Test end-to-end episode processing
3. Add integration tests
4. Implement production monitoring
5. Document troubleshooting procedures 