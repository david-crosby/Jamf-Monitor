# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2024-12-07

### Added
- Database support with automatic SQLite/MySQL switching
- Device health caching with configurable TTL
- Persistent settings storage (thresholds, compliance groups, monitored groups)
- Database migration support with Alembic
- Comprehensive logging throughout application
- Password strength validation
- Token refresh endpoint
- Force refresh option to bypass cache
- Cache control via API query parameters
- Startup validation for secret key
- Database initialisation script
- User repository for future multi-user support

### Changed
- Settings now persist across application restarts
- Improved error handling in Jamf API service
- Enhanced authentication with better error messages
- Updated API service to handle token expiry
- Dashboard now shows cache status and control
- Improved API documentation

### Fixed
- Settings no longer lost on restart
- Better error messages for authentication failures
- Proper password hashing validation
- Token expiry handling in frontend
- Missing error logging in async operations

### Security
- Admin password now properly validated as bcrypt hash
- Secret key validation on startup
- Password strength requirements documented
- Session handling improved with proper token management

## [1.0.0] - 2024-12-01

### Added
- Initial release
- Real-time device health monitoring
- RAG status indicators (Red/Amber/Green)
- Configurable health check thresholds
- Smart group compliance monitoring
- JWT-based authentication
- Dashboard with status cards and device table
- Settings panel for threshold configuration
- Auto-refresh functionality
- Jamf Pro API integration
- React frontend with TypeScript
- FastAPI backend
- Basic error handling
- CORS support

### Security
- JWT token authentication
- Secure password hashing with bcrypt
- Environment-based configuration
