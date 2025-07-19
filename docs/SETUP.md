# PodcastPro v2 - Development Setup

## Current Status (July 18, 2025)
**Environment**: Windows 11, Python 3.13, Flask 3.0.0  
**Database**: SQLite (development), PostgreSQL (production)  
**Status**: Core systems working, debugging final issues  

## Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/tgdscott/pod2.git AAAPodcastPro
cd AAAPodcastPro
```

### 2. Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Setup
```bash
# Create database (already exists with test data)
python recreate_database.py

# Or use existing database
# podcastpro_dev.db is already configured
```

### 4. Environment Configuration
```bash
# Copy environment file
copy .env.example .env

# Edit .env file with your settings
```

### 5. Start Development Server
```bash
python run.py
```

Server will start on http://localhost:5000

## Test the Installation

### Quick Health Check
```bash
curl http://localhost:5000/api/v1/health
```

### Run Test Suite
```bash
# Comprehensive end-to-end test
python test_real_world.py

# Expected: 3/7 tests passing (current state)
```

### Test Authentication
```bash
# Test protected endpoints
python test_protected_endpoints.py
```

## Current Working Features

### ✅ Fully Functional
- User registration and login
- JWT authentication
- Podcast CRUD operations
- Episode CRUD operations
- Protected endpoints
- Database operations
- Error handling

### ⚡ In Development
- File upload system
- Background processing
- Audio file processing

## Development Environment

### Required Tools
- Python 3.13
- Git
- Text editor (VS Code recommended)
- curl (for API testing)

### Python Dependencies
```
flask==3.0.0
flask-jwt-extended==4.6.0
flask-cors==4.0.0
bcrypt==4.1.2
requests==2.31.0
sqlalchemy==2.0.23
python-dotenv==1.0.0
```

## Database Schema

### Current Tables
- **users**: User accounts with authentication
- **podcasts**: Podcast metadata and settings
- **episodes**: Episode information and status
- **jobs**: Background job tracking
- **user_files**: File upload management
- **templates**: Episode templates

### Test Data
- **User**: realworld@test.com / RealWorld123!
- **Podcast**: "Real World Test Podcast"
- **Episodes**: Multiple test episodes

## API Testing

### Authentication Flow
```bash
# Register user
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123","username":"testuser"}'

# Login
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'

# Use returned JWT token in subsequent requests
```

### Protected Endpoints
```bash
# Get user's podcasts
curl -X GET http://localhost:5000/api/v1/podcasts \
  -H "Authorization: Bearer <jwt_token>"

# Create podcast
curl -X POST http://localhost:5000/api/v1/podcasts \
  -H "Authorization: Bearer <jwt_token>" \
  -H "Content-Type: application/json" \
  -d '{"title":"My Podcast","description":"Test podcast"}'
```

## Common Issues & Solutions

### Server Won't Start
- Check Python version (3.13 required)
- Verify virtual environment is activated
- Check for port conflicts (5000)

### Database Errors
- Recreate database: `python recreate_database.py`
- Check file permissions on `podcastpro_dev.db`

### Authentication Failures
- Check JWT secret key in .env
- Verify token format in requests
- Check token expiration

## File Structure
```
AAAPodcastPro/
├── src/
│   ├── api/                 # API endpoints
│   │   ├── auth.py         # Authentication
│   │   ├── podcasts.py     # Podcast management
│   │   ├── episodes.py     # Episode management
│   │   └── files.py        # File upload
│   ├── database/           # Database models
│   │   ├── models.py       # Production models
│   │   └── models_dev.py   # Development models
│   └── core/               # Core processing
├── tests/                  # Test files
├── docs/                   # Documentation
└── uploads/                # File uploads
```

## Next Steps
1. Fix file upload issues
2. Configure Celery for background jobs
3. Complete audio processing pipeline
4. Deploy to production

## Support
- Check test results with `python test_real_world.py`
- Review server logs for errors
- See PROJECT_COMPLETE.md for current status