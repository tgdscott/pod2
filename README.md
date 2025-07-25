# PodcastPro

A Flask-based podcast processing application with background job processing using Celery and Redis.

## Current Status: Docker Infrastructure Complete, Celery Import Blocker

### What's Working ✅
- **Docker Infrastructure**: Multi-service setup with Redis, Flask, and Celery
- **Flask Application**: Running successfully in Docker container on port 5000
- **Redis Service**: Running and accessible to other containers
- **Volume Mounts**: uploads/, outputs/, test_files/, database working correctly
- **Environment Configuration**: .env file loading and environment variables working
- **System Dependencies**: All required packages (libpq-dev, ffmpeg, libsndfile1) installed
- **Python Environment**: Python 3.11 working correctly in container

### Current Blocker ❌
- **Celery Worker**: Cannot import core.celery_worker module in Docker container
- **Error**: ModuleNotFoundError: No module named 'core.celery_worker'
- **Impact**: Background episode processing completely non-functional
- **Root Cause**: core/celery_worker.py file missing from Docker container

## Quick Start

### Prerequisites
- Docker and Docker Compose
- Python 3.11 compatibility

### Running the Application

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd AAAPodcastPro
   ```

2. **Set up environment variables**
   ```bash
   # Create .env file with:
   REDIS_URL=redis://redis:6379/0
   CELERY_BROKER_URL=redis://redis:6379/0
   ```

3. **Build and start services**
   ```bash
   docker-compose build
   docker-compose up
   ```

4. **Access the application**
   - Web UI: http://localhost:5000
   - API: http://localhost:5000/api

## Project Structure

```
AAAPodcastPro/
├── src/
│   ├── api/           # Flask API endpoints
│   ├── core/          # Core processing logic
│   ├── database/      # Database models and configuration
│   └── web/           # Web templates and static files
├── uploads/           # Uploaded audio files
├── outputs/           # Processed output files
├── test_files/        # Test audio files
├── docker-compose.yml # Multi-service orchestration
├── Dockerfile         # Container configuration
└── requirements.txt   # Python dependencies
```

## Services

### Flask Web Application
- **Port**: 5000
- **Status**: ✅ Working
- **Purpose**: API endpoints and web interface

### Redis Service
- **Port**: 6379
- **Status**: ✅ Working
- **Purpose**: Message broker for Celery

### Celery Worker
- **Status**: ❌ Blocked (import error)
- **Purpose**: Background job processing
- **Issue**: core/celery_worker.py missing from container

## Current Issues

### Critical: Celery Worker Import
- **Problem**: core/celery_worker.py missing from Docker container
- **Investigation Needed**: Check .dockerignore and build context
- **Fix Required**: Ensure file is copied to container during build

### Background Processing
- **Status**: Non-functional due to Celery import issue
- **Impact**: Episode processing cannot complete
- **Dependencies**: Redis, Celery worker, task registration

## Development

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask development server
python run.py
```

### Docker Development
```bash
# Build and start all services
docker-compose up --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Testing
```bash
# Test in container
docker run -it --rm -w /app/src aaapodcastpro:latest python -c "import core.celery_worker"
```

## Configuration

### Environment Variables
- `REDIS_URL`: Redis connection string
- `CELERY_BROKER_URL`: Celery broker URL
- `DATABASE_URL`: Database connection string

### Docker Configuration
- **Base Image**: python:3.11-slim
- **Working Directory**: /app/src
- **Python Path**: /app/src
- **System Dependencies**: libpq-dev, ffmpeg, libsndfile1

## Troubleshooting

### Common Issues

#### Port Already Allocated
```bash
docker ps
docker stop <container_id>
```

#### Celery Import Errors
```bash
# Check container contents
docker run -it --rm -w /app/src aaapodcastpro:latest ls -la core/

# Test imports
docker run -it --rm -w /app/src aaapodcastpro:latest python -c "import core.celery_worker"
```

#### Redis Connection Issues
- Verify .env file contains correct Redis URLs
- Check Docker network connectivity
- Ensure Redis service is running

## Next Steps

1. **Resolve Celery worker import issue**
   - Fix Docker build context
   - Ensure core/celery_worker.py is in container
   - Test Celery worker startup

2. **Achieve end-to-end processing**
   - Test with real audio files
   - Verify background job execution
   - Add error handling and logging

3. **Production readiness**
   - Add monitoring and health checks
   - Implement security measures
   - Complete documentation

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License.
