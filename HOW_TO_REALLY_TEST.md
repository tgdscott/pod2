# How to Really Test PodcastPro v2

## Current Testing Status (July 18, 2025)
**Real-World Test Results**: 3/7 tests passing  
**Server Status**: Running on localhost:5000  
**Database**: SQLite with synchronized models  

## Quick Test Commands

### 1. Start the Server
```bash
cd D:\AAAPodcastPro
python run.py
```
Server should start on http://localhost:5000

### 2. Run Comprehensive End-to-End Test
```bash
python test_real_world.py
```

**Expected Output**:
- ✅ User Registration/Login
- ✅ Podcast Creation (handles duplicates)
- ❌ File Upload (debugging 'filename' error)
- ✅ Episode Creation 
- ❌ Episode Processing (debugging background jobs)
- ✅ Data Retrieval
- ✅ Error Handling

### 3. Test Protected Endpoints
```bash
python test_protected_endpoints.py
```

### 4. Test Authentication Flow
```bash
python test_auth_debug.py
```

## Current Issues Being Debugged

### File Upload Issue
- **Error**: `'filename'` attribute error
- **Location**: `src/api/files.py`
- **Issue**: UserFile model missing `filename` property
- **Fix**: Use `original_filename` or `stored_filename`

### Episode Processing Issue
- **Error**: Background processing starts but fails
- **Location**: `src/api/episodes.py`
- **Issue**: Celery task queue not properly configured
- **Status**: Basic structure working, needs Celery setup

## Test Files Available

1. **test_real_world.py** - Comprehensive end-to-end testing
2. **test_protected_endpoints.py** - JWT protected route testing  
3. **test_auth_debug.py** - Authentication flow testing
4. **test_api_basic.py** - Basic API endpoint testing

## Database Status
- **File**: `podcastpro_dev.db`
- **Models**: Synchronized between `models.py` and `models_dev.py`
- **Users**: Test user `realworld@test.com` exists
- **Podcasts**: Test podcast "Real World Test Podcast" exists
- **Episodes**: Multiple test episodes created

## Next Steps
1. Fix file upload `filename` attribute error
2. Configure Celery for background processing
3. Test audio file processing pipeline
4. Achieve 7/7 test success rate
5. Deploy to production environment

## Emergency Commands
```bash
# Check server status
curl http://localhost:5000/api/v1/health

# Check database
python -c "from src.database import get_db_session; print('DB OK')"

# Reset database if needed
python recreate_database.py

# Check git status
git status
```

## Test Data
- **Test User**: `realworld@test.com` / `RealWorld123!`
- **Test Podcast**: "Real World Test Podcast"
- **Test Episodes**: "Real World Test Episode"
- **API Base URL**: `http://localhost:5000/api/v1`

## Success Criteria
- All 7 real-world tests passing
- File upload working with valid audio files
- Episode processing completing successfully
- Background jobs completing
- No Python errors in server logs