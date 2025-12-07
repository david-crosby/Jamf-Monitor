# Quick Start Guide

## Development Setup (5 minutes)

### 1. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux

# Install dependencies
uv pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your Jamf credentials
# At minimum, set: JAMF_URL, JAMF_CLIENT_ID, JAMF_CLIENT_SECRET

# Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Add the output to SECRET_KEY in .env

# Initialise database
python -m app.scripts.init_db

# Start backend
uvicorn app.main:app --reload
```

Backend will be available at `http://localhost:8000`

### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start frontend
npm run dev
```

Frontend will be available at `http://localhost:3000`

### 3. Log In

Default credentials:
- Username: `admin`
- Password: `changeme`

**Important:** Change these in production!

## Production Deployment

See [DATABASE_IMPLEMENTATION_GUIDE.md](DATABASE_IMPLEMENTATION_GUIDE.md) for complete production setup including MySQL configuration.

### Key Production Steps

1. Set `ENVIRONMENT=production` in `.env`
2. Configure MySQL database
3. Set secure `SECRET_KEY` and `ADMIN_PASSWORD`
4. Run migrations: `alembic upgrade head`
5. Deploy behind reverse proxy with HTTPS
6. Configure proper CORS origins

## Common Tasks

### Updating Thresholds

Via UI: Settings button → Adjust values → Save

Via API:
```bash
curl -X PUT http://localhost:8000/api/v1/settings/thresholds \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"check_in_hours": 48, "recon_hours": 24, "pending_command_hours": 6}'
```

### Force Refresh from Jamf

Via UI: "Force Refresh" button

Via API:
```bash
curl http://localhost:8000/api/v1/devices/?use_cache=false \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Database Migrations

```bash
cd backend

# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Troubleshooting

### Backend won't start
- Check `.env` file exists and has required variables
- Verify virtual environment is activated
- Check database file permissions

### Frontend won't connect
- Verify backend is running on port 8000
- Check CORS settings in backend `.env`
- Check browser console for errors

### Database errors
- Ensure database is initialised: `python -m app.scripts.init_db`
- Check file permissions on `jamf_monitor.db`
- For MySQL: verify connection settings and user permissions

### Authentication fails
- Verify Jamf credentials in `.env`
- Check admin password is bcrypt hash
- Ensure SECRET_KEY is set

## Next Steps

1. Review [CODE_REVIEW.md](CODE_REVIEW.md) for recommendations
2. Read [DATABASE_IMPLEMENTATION_GUIDE.md](DATABASE_IMPLEMENTATION_GUIDE.md) for details
3. Configure monitored smart groups
4. Set up production deployment
5. Implement recommended security improvements
