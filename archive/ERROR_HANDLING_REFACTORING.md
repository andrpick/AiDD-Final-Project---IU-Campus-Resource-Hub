# Error Handling & Logging Refactoring Summary

## Overview
This document summarizes the comprehensive error handling and logging improvements implemented across the codebase.

## Changes Made

### 1. Custom Exception Classes (`src/utils/exceptions.py`)
Created a hierarchy of custom exceptions for better error categorization:
- `CampusResourceHubError`: Base exception class
- `ValidationError`: Input validation failures
- `NotFoundError`: Resource not found errors
- `ConflictError`: Booking conflicts (includes conflict details)
- `AuthorizationError`: Permission/authorization failures
- `DatabaseError`: Database operation failures
- `BookingError`: Booking-specific errors
- `ResourceError`: Resource-specific errors
- `AuthenticationError`: Authentication failures

### 2. Structured Logging (`src/utils/logging_config.py`)
Implemented comprehensive logging configuration:
- **Console Handler**: Simple format for development
- **File Handler**: Detailed format with function names and line numbers (rotating, 10MB max)
- **Error File Handler**: Separate file for errors only
- **Log Levels**: Configurable via `LOG_LEVEL` environment variable (defaults to INFO, DEBUG if FLASK_DEBUG=1)
- **Suppressed Noisy Loggers**: Werkzeug and dateutil warnings reduced

### 3. Database Layer Improvements (`src/data_access/database.py`)
- Replaced bare `except Exception:` with specific `sqlite3.Error` handling
- Added logging for connection failures and operation errors
- Raises `DatabaseError` with proper error context
- Maintains transaction rollback on errors

### 4. Service Layer Improvements

#### Booking Service (`src/services/booking_service.py`)
- Added logging for booking creation, conflicts, and status updates
- Specific exception handling for datetime parsing (`ValueError`, `TypeError`)
- Warning logs for invalid operations (booking not found, invalid status)
- Info logs for successful operations

#### AI Concierge (`src/services/ai_concierge.py`)
- Replaced `print()` statements with proper logging
- Error logging with full traceback for API failures
- Structured error handling

### 5. Utility Functions Improvements

#### Datetime Utils (`src/utils/datetime_utils.py`)
- Specific exception handling: `ValueError`, `TypeError`, `AttributeError`
- Warning logs for parsing/formatting failures
- Better error messages with context

#### HTML Utils (`src/utils/html_utils.py`)
- Updated to use centralized logging configuration
- Specific exception handling for unescaping operations

#### JSON Utils (`src/utils/json_utils.py`)
- Updated to use centralized logging configuration
- Already had proper exception handling

#### Calendar Service (`src/services/calendar_service.py`)
- Added logging configuration
- Specific exception handling for date parsing errors

### 6. Application Entry Point (`app.py`)
- Logging initialization on startup
- Startup logs for configuration (database path, upload folder)
- Proper logging setup before Flask app initialization

## Benefits

1. **Better Debugging**: Detailed logs with function names, line numbers, and full stack traces
2. **Production Monitoring**: Separate error log file for easy monitoring
3. **Error Categorization**: Custom exceptions make error handling more precise
4. **Maintainability**: Centralized logging configuration
5. **Performance**: Rotating log files prevent disk space issues
6. **Security**: Sensitive errors logged appropriately without exposing internals

## Log Files

Logs are written to the `logs/` directory:
- `campus_resource_hub.log`: All log entries (DEBUG and above)
- `errors.log`: Only ERROR and CRITICAL entries

## Environment Variables

- `LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `FLASK_DEBUG`: If set to '1', automatically sets LOG_LEVEL to DEBUG

## Testing

All 52 tests continue to pass after these changes, confirming backward compatibility.

## Future Improvements

1. Add structured logging with JSON format for production
2. Implement log aggregation for distributed deployments
3. Add metrics/monitoring integration (e.g., Sentry, DataDog)
4. Create error reporting middleware for Flask
5. Add request ID tracking for better traceability

