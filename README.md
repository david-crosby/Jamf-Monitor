# Jamf Monitor

A single pane of glass for monitoring macOS device health in Jamf Pro. This application provides real-time visibility into device compliance, MDM command status, and policy execution.

## Features

- **RAG Status Monitoring**: Visual health indicators (Red/Amber/Green) for quick device status assessment
- **Real-time Dashboard**: Live updates on device check-in status, recon execution, and MDM command status
- **Configurable Thresholds**: Customisable time windows for health checks
- **Smart Group Integration**: Monitor device compliance and group membership
- **Secure Authentication**: JWT-based authentication with proper security practices
- **Scalable Architecture**: Built with FastAPI and React for performance and maintainability

## Health Metrics

### Unhealthy (Red)
- Device hasn't checked in within the configured threshold
- Device hasn't run recon within the configured threshold
- Device has failed policies
- Device has failed MDM commands/profiles
- Device has pending MDM commands exceeding the threshold

### Caution (Amber)
- Device is out of compliance (not in compliance smart group)
- Device is member of monitored smart groups

### Healthy (Green)
- All health checks pass

## Prerequisites

- Python 3.11+
- Node.js 18+
- Jamf Pro instance with API credentials
- macOS (recommended) or Linux for development

## Backend Setup

1. Navigate to the backend directory:
```bash
cd backend
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
pip install --break-system-packages -r requirements.txt
```

Or using uv:
```bash
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

3. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

4. Configure your environment variables:
```env
JAMF_URL=https://your-instance.jamfcloud.com
JAMF_CLIENT_ID=your_client_id
JAMF_CLIENT_SECRET=your_client_secret
SECRET_KEY=your_generated_secret_key
```

Generate a secure secret key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

5. Run the backend:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

## Frontend Setup

1. Navigate to the frontend directory:
```bash
cd frontend
```

2. Install dependencies:
```bash
npm install
```

3. Create a `.env` file:
```bash
cp .env.example .env
```

4. Run the development server:
```bash
npm run dev
```

The application will be available at `http://localhost:3000`

## Default Credentials

```
Username: admin
Password: changeme
```

**Important**: Change these credentials in production by modifying the password hash in `backend/app/api/routes/auth.py`

## API Documentation

Once the backend is running, visit:
- Swagger UI: `http://localhost:8000/api/v1/docs`
- ReDoc: `http://localhost:8000/api/v1/redoc`

## Configuration

### Health Check Thresholds

Adjust these values in the Settings panel or via environment variables:

- `CHECK_IN_THRESHOLD_HOURS`: Maximum hours since last check-in (default: 24)
- `RECON_THRESHOLD_HOURS`: Maximum hours since last recon (default: 24)
- `PENDING_COMMAND_THRESHOLD_HOURS`: Maximum hours for pending commands (default: 6)

### Monitored Smart Groups

Configure which smart groups trigger caution status in the Settings panel.

## Security Considerations

1. **Credentials**: Store Jamf credentials securely using environment variables
2. **Secret Key**: Use a strong, randomly generated secret key
3. **HTTPS**: Deploy behind a reverse proxy with TLS in production
4. **Authentication**: JWT tokens expire after 30 minutes by default
5. **CORS**: Configure appropriate origins in production

## Production Deployment

1. Set `DEBUG=False` in production
2. Use a production-grade ASGI server (e.g., gunicorn with uvicorn workers)
3. Configure a reverse proxy (nginx/Apache)
4. Enable HTTPS
5. Implement proper logging and monitoring
6. Consider adding SSO integration (future enhancement)

## Project Structure

```
jamf-monitor/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/      # API endpoints
│   │   ├── core/            # Configuration and security
│   │   ├── models/          # Data models
│   │   ├── services/        # Business logic
│   │   └── main.py          # Application entry point
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── components/      # React components
    │   ├── pages/           # Page components
    │   ├── services/        # API communication
    │   ├── types/           # TypeScript definitions
    │   └── utils/           # Helper functions
    └── package.json
```

## Troubleshooting

### bcrypt Compatibility Issues

If you encounter bcrypt compatibility issues, ensure you're using bcrypt 4.0.1:
```bash
pip uninstall bcrypt
pip install --break-system-packages bcrypt==4.0.1
```

### CORS Errors

Ensure the frontend URL is added to `CORS_ORIGINS` in the backend `.env` file.

### Authentication Failures

Check that:
1. Jamf Pro credentials are correct
2. API client has appropriate permissions
3. JWT secret key is configured

## Future Enhancements

- SSO integration (SAML/OAuth)
- Email notifications for critical issues
- Historical trending and analytics
- Custom alert rules
- Mobile app support

## Contributing

This is a learning project. Contributions are welcome via pull requests.

## Licence

MIT Licence

## Support

For issues or questions, please open an issue on the project repository.
