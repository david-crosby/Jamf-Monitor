# Code Review: Jamf Monitor

## Overview

This is a well-structured FastAPI + React application for monitoring macOS device health in Jamf Pro. The code follows modern Python and TypeScript practices, but there are several areas for improvement.

## Critical Issues

### 1. Password Storage in Environment Variables
**Location**: `backend/app/core/config.py`, `backend/app/api/routes/auth.py`

The admin password is stored as a plain string in environment variables and compared using `verify_password`. This suggests the `.env` file should contain a **hashed** password, but the `.env.example` shows `ADMIN_PASSWORD=changeme` which is plaintext.

**Impact**: If users follow the example, passwords will be stored in plaintext.

**Recommendation**: Either hash the password during application startup or document clearly that the environment variable must contain a bcrypt hash.

### 2. In-Memory Settings Loss
**Location**: `backend/app/services/health_service.py`

Settings like `compliance_group_name` and `monitored_groups` are stored in memory on the service instance. These will be lost on application restart.

**Impact**: Configuration persistence is unreliable.

**Recommendation**: Implement database storage for application settings (addressed in database implementation below).

### 3. No Request Rate Limiting
**Location**: All API endpoints

There's no rate limiting on API endpoints, particularly the authentication endpoint.

**Impact**: Vulnerable to brute force attacks and API abuse.

**Recommendation**: Implement rate limiting using `slowapi` or similar.

### 4. Uncached Jamf API Calls
**Location**: `backend/app/services/health_service.py` - `check_all_devices()`

Every dashboard load triggers API calls to Jamf Pro for all devices. This is inefficient and can hit Jamf API rate limits.

**Impact**: Slow performance and potential API throttling.

**Recommendation**: Implement caching with the database solution.

## High Priority Issues

### 5. Error Handling in Async Gather
**Location**: `backend/app/services/health_service.py:93`

```python
results = await asyncio.gather(*tasks, return_exceptions=True)
return [r for r in results if isinstance(r, DeviceHealth)]
```

Exceptions are silently discarded. Failed device checks won't be logged or reported.

**Recommendation**: Log exceptions and optionally return partial results with error indicators.

### 6. LRU Cache on Async Functions
**Location**: `backend/app/services/health_service.py:134`, `backend/app/services/jamf_service.py:181`

Using `@lru_cache()` on functions that return service instances is problematic because the cache doesn't account for the function being a dependency injection factory.

**Recommendation**: Use proper dependency injection without caching, or use `functools.cache` for singleton pattern.

### 7. Hardcoded Credentials Display
**Location**: `frontend/src/pages/LoginPage.tsx:125-130`

Default credentials are displayed on the login page in production.

**Recommendation**: Only show in development mode or remove entirely.

### 8. No Input Validation on Threshold Updates
**Location**: `backend/app/api/routes/settings.py:18-26`

The `set_thresholds` method accepts `None` values but then checks `if check_in_hours:` which fails for `0`.

**Recommendation**: Use explicit `is not None` checks or require all values.

### 9. British English Inconsistency
**Location**: Various files

The codebase uses American English spelling (e.g., "Unauthorized", "color") but user preferences specify British English.

**Recommendation**: Standardise to British English throughout (unauthorised, colour, etc.).

## Medium Priority Issues

### 10. No Timezone Handling in Frontend
**Location**: `frontend/src/utils/helpers.ts`

Date formatting doesn't account for user timezone, using local timezone implicitly.

**Recommendation**: Either standardise on UTC display or show times in user's local timezone with clear indication.

### 11. Token Refresh Not Implemented
**Location**: `frontend/src/services/api.ts`

JWT tokens expire after 30 minutes but there's no automatic refresh mechanism.

**Recommendation**: Implement token refresh before expiry or handle 401 errors with re-authentication.

### 12. No Loading State During Threshold Updates
**Location**: `frontend/src/pages/Dashboard.tsx`

Settings updates don't show loading state, making the UX unclear.

**Recommendation**: Add loading indicators during async operations.

### 13. CORS Origins Hardcoded
**Location**: `backend/app/core/config.py:18`

CORS origins default to localhost, which won't work in production.

**Recommendation**: Remove defaults and require explicit configuration.

## Low Priority Issues

### 14. Magic Numbers
**Location**: Throughout codebase

Various magic numbers (e.g., 60000ms for refresh interval, 30.0s for timeout) should be constants.

### 15. Inconsistent Error Messages
**Location**: API error responses

Error messages vary in format and detail level.

**Recommendation**: Standardise error response structure.

### 16. No API Versioning Strategy
**Location**: `backend/app/main.py`

API version is in the path but there's no clear migration strategy.

**Recommendation**: Document versioning policy.

### 17. Frontend Type Safety
**Location**: `frontend/src/services/api.ts`

API responses aren't validated at runtime, relying only on TypeScript types.

**Recommendation**: Consider using Zod or similar for runtime validation.

## Security Considerations

### 18. JWT Secret Key Generation
**Location**: `backend/app/core/config.py`

The README suggests generating a secret key but doesn't enforce minimum entropy.

**Recommendation**: Validate secret key length/complexity on startup.

### 19. No HTTPS Enforcement
**Location**: API and frontend configuration

No redirect from HTTP to HTTPS in production guidance.

**Recommendation**: Add HTTPS enforcement in production deployment documentation.

## Code Quality

### Positive Aspects
- Clean separation of concerns with services, routes, and models
- Proper use of Pydantic for validation
- TypeScript for type safety in frontend
- Async/await used correctly
- Reasonable error handling in most places

### Areas for Improvement
- Add docstrings to all public methods
- Increase test coverage (no tests present)
- Add logging throughout the application
- Consider adding OpenAPI examples for better API documentation

## Performance Considerations

### 20. Synchronous Dependency Injection
**Location**: All route handlers

FastAPI's dependency injection is called synchronously even with async routes.

**Recommendation**: Ensure no blocking operations in dependencies.

### 21. No Connection Pooling Configuration
**Location**: `backend/app/services/jamf_service.py`

HTTP client doesn't configure connection pooling limits.

**Recommendation**: Configure `httpx.AsyncClient` with appropriate limits.

## Recommendations Summary

**Immediate Actions Required**:
1. Implement database for persistent settings storage
2. Fix password storage documentation
3. Add rate limiting to auth endpoints
4. Implement caching for Jamf API calls
5. Improve error handling in async operations

**Short-term Improvements**:
1. Add comprehensive logging
2. Implement token refresh mechanism
3. Remove hardcoded credentials from login page
4. Standardise British English spelling
5. Add input validation throughout

**Long-term Enhancements**:
1. Add unit and integration tests
2. Implement proper monitoring and alerting
3. Add API rate limiting across all endpoints
4. Consider implementing proper user management
5. Add historical trending data storage

## Overall Assessment

**Grade**: B+

The codebase demonstrates good understanding of modern web development practices with clean architecture and proper separation of concerns. However, the lack of persistent storage, testing, and some security considerations prevent this from being production-ready. The database implementation (next section) will address several critical issues.
