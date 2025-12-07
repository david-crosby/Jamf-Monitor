# Database Implementation Guide

## Overview

This implementation adds persistent database storage to the Jamf Monitor application. The system automatically switches between SQLite (development) and MySQL (production) based on the `ENVIRONMENT` setting.

## What's Been Added

### New Files

1. **`backend/app/core/database.py`** - Database configuration and session management
2. **`backend/app/core/db_models.py`** - SQLAlchemy database models
3. **`backend/app/core/repositories.py`** - Repository pattern for database operations
4. **`backend/app/scripts/init_db.py`** - Database initialisation script
5. **`backend/alembic/`** - Database migrations directory
6. **`backend/alembic.ini`** - Alembic configuration

### Updated Files

The following files need to be updated in your project:

1. **`backend/requirements.txt`** - Add database dependencies
2. **`backend/app/core/config.py`** - Add database configuration
3. **`backend/app/services/health_service.py`** - Add database caching
4. **`backend/app/api/routes/settings.py`** - Use database for settings
5. **`backend/app/api/routes/devices.py`** - Add cache control parameters
6. **`backend/.env.example`** - Add database configuration

## Database Models

### ApplicationSettings
Stores key-value configuration that persists across restarts.

### HealthThreshold
Stores health check threshold configurations with history.

### CachedDeviceHealth
Caches device health data to reduce Jamf API calls.

### User
Stores user authentication data for future multi-user support.

## Setup Instructions

### Development (SQLite)

1. **Install dependencies**:
```bash
cd backend
uv pip install -r requirements.txt
```

2. **Update environment configuration**:
```bash
cp .env.example .env
# Edit .env and ensure ENVIRONMENT=development
```

3. **Initialise the database**:
```bash
python -m app.scripts.init_db
```

4. **Run the application**:
```bash
uvicorn app.main:app --reload
```

The SQLite database will be created at `./jamf_monitor.db`.

### Production (MySQL)

1. **Create MySQL database**:
```sql
CREATE DATABASE jamf_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'jamf_monitor'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON jamf_monitor.* TO 'jamf_monitor'@'localhost';
FLUSH PRIVILEGES;
```

2. **Update environment configuration**:
```bash
cp .env.example .env
```

Edit `.env`:
```bash
ENVIRONMENT=production

MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=jamf_monitor
MYSQL_PASSWORD=secure_password
MYSQL_DATABASE=jamf_monitor
```

3. **Run database migrations**:
```bash
cd backend
alembic upgrade head
```

4. **Create default settings**:
```bash
python -m app.scripts.init_db
```

## Database Migrations

### Creating a New Migration

When you modify database models:

```bash
cd backend
alembic revision --autogenerate -m "Description of changes"
```

### Applying Migrations

```bash
alembic upgrade head
```

### Rolling Back

```bash
alembic downgrade -1  # Roll back one migration
alembic downgrade base  # Roll back all migrations
```

## Key Features

### Automatic Database Switching

The application automatically uses the appropriate database based on `ENVIRONMENT`:
- `development` → SQLite
- `production` → MySQL

No code changes required.

### Settings Persistence

Application settings now persist across restarts:
- Health check thresholds
- Compliance group name
- Monitored groups list

### Device Health Caching

Device health data is cached in the database to reduce Jamf API calls:
- Default cache TTL: 300 seconds (5 minutes)
- Configurable via `CACHE_TTL_SECONDS`
- Can be bypassed with `use_cache=false` query parameter

### API Changes

#### New Query Parameters

All device endpoints now accept:
- `use_cache` (boolean, default: true) - Use cached data if available

Examples:
```bash
# Use cache (default)
GET /api/v1/devices/

# Force fresh data from Jamf
GET /api/v1/devices/?use_cache=false

# Get single device without cache
GET /api/v1/devices/123?use_cache=false
```

## Performance Considerations

### Cache Benefits

With caching enabled:
- Dashboard loads are significantly faster
- Reduced Jamf API calls prevents rate limiting
- Lower latency for end users

### Cache Invalidation

Cache entries automatically expire based on TTL. To force a refresh:
1. Use `use_cache=false` query parameter
2. Wait for cache to expire naturally
3. Restart the application (clears in-memory caches)

## Backwards Compatibility

The implementation maintains backwards compatibility:
- Works without database (falls back to in-memory storage)
- Existing API endpoints unchanged
- No breaking changes to frontend

## Troubleshooting

### SQLite Permission Errors

```bash
# Ensure write permissions
chmod 644 jamf_monitor.db
```

### MySQL Connection Errors

Check:
1. MySQL service is running
2. Credentials are correct in `.env`
3. Database exists
4. User has appropriate permissions

```bash
# Test connection
mysql -h localhost -u jamf_monitor -p jamf_monitor
```

### Migration Conflicts

If migrations fail:
```bash
# Check current migration state
alembic current

# Show migration history
alembic history

# Force to specific revision
alembic stamp head
```

## Security Notes

### Password Hashing

The `ADMIN_PASSWORD` in `.env` should be a bcrypt hash:

```python
from passlib.context import CryptContext
ctx = CryptContext(schemes=["bcrypt"])
print(ctx.hash("your_password"))
```

### Database Credentials

Never commit:
- `.env` files
- SQLite database files
- MySQL credentials

Always use environment variables in production.

## Testing

### Testing SQLite Setup

```bash
cd backend
python -m app.scripts.init_db
pytest tests/  # When tests are added
```

### Testing MySQL Setup

```bash
ENVIRONMENT=production python -m app.scripts.init_db
```

## Future Enhancements

Potential improvements:
1. Add database connection pooling configuration
2. Implement read replicas for scaling
3. Add database backup scripts
4. Create historical trending tables
5. Implement audit logging

## Migration from Current System

### Step 1: Back Up Current Data

Before migrating, document:
- Current threshold settings
- Compliance group name
- Monitored groups list

### Step 2: Install Database

Follow setup instructions above for your environment.

### Step 3: Configure Settings

After initialisation, update settings via API or directly in database to match your previous configuration.

### Step 4: Verify

Test that:
- Settings persist after restart
- Device health data is cached
- API responses match previous behaviour

## Support

For issues with database implementation:
1. Check logs for detailed error messages
2. Verify environment configuration
3. Ensure dependencies are installed
4. Check database permissions

## Summary of Changes

| Component | Change | Impact |
|-----------|--------|--------|
| Configuration | Added database settings | Must update `.env` |
| Dependencies | Added SQLAlchemy, Alembic, database drivers | Must reinstall |
| Settings | Now persist in database | No longer lost on restart |
| Device Health | Cached in database | Faster API responses |
| Thresholds | Stored with history | Can track changes |
| Users | Table created | Ready for multi-user |

## Additional Notes

### Why This Architecture?

- **Repository Pattern**: Separates database logic from business logic
- **Async Operations**: Maintains FastAPI's async benefits
- **Flexible Storage**: Easy to switch databases
- **Migration Support**: Alembic handles schema changes gracefully

### Performance Impact

Expected improvements:
- Initial load: Same (requires Jamf API call)
- Subsequent loads: 50-80% faster (uses cache)
- API response times: 100-500ms → 10-50ms with cache

### Monitoring

Consider adding:
- Cache hit/miss metrics
- Database query performance logging
- Connection pool statistics
