# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
python app.py
```
Application runs on `http://localhost:5000` (configurable via `FLASK_HOST` and `FLASK_PORT` in `.env`)

### Testing
```bash
# Run all tests (139 tests with coverage reporting)
python tests/run_tests.py

# Run specific test file
python -m pytest tests/test_booking_service.py -v

# Run tests without coverage
python -m pytest tests/ -v
```

### Database Initialization
```bash
# Recreate database from scratch (WARNING: deletes existing data)
python init_db.py
```
Note: The repository includes `campus_resource_hub.db` with sample data. Only run `init_db.py` if you need a fresh database.

### Environment Setup
```bash
# Copy environment template
cp .env.example .env

# Generate secure SECRET_KEY for .env
python -c "import secrets; print(secrets.token_hex(32))"
```

## Architecture Overview

### Layered Architecture (MVC + Service Layer)

**Controllers** (`src/controllers/`) - HTTP request handling, route definitions
- Flask blueprints: `auth`, `resources`, `bookings`, `messages`, `reviews`, `admin`, `ai_concierge`, `search`
- Use `controller_helpers.py` for common patterns (permission checks, image handling)
- Controllers call service layer, never access database directly

**Services** (`src/services/`) - Business logic layer
- Core services: `auth_service`, `resource_service`, `booking_service`, `messaging_service`, `review_service`, `search_service`, `admin_service`, `ai_concierge`
- Return standardized dict: `{'success': bool, 'data': dict}` or `{'success': bool, 'error': str}`
- Services use data access layer for database operations

**Data Access** (`src/data_access/database.py`) - Database abstraction
- `get_db_connection()` context manager for all database operations
- SQLite with `row_factory = sqlite3.Row` for dict-like access
- Automatic transaction management (commit on success, rollback on error)

**Models** (`src/models/`) - Data models with Flask-Login integration
- `User` model with role-based methods: `is_admin()`, `is_staff()`

**Views** (`src/views/`) - Jinja2 templates with Bootstrap 5

### Database Schema
- **users**: User accounts with role-based access (student/staff/admin)
- **resources**: Campus resources (study rooms, equipment, etc.) with multi-image support
- **bookings**: Resource reservations with time-based conflict detection
- **messages**: Thread-based messaging system with resource-specific threads
- **reviews**: Resource ratings (1-5 stars) tied to completed bookings
- **thread_read**: Unread message tracking per user per thread
- **admin_logs**: Audit trail for admin actions

See `docs/context/ERD_AND_SCHEMA.md` for complete schema details.

## Key Utilities

### Controller Helpers (`src/utils/controller_helpers.py`)
Essential helpers for controllers to reduce code duplication:
- `check_resource_permission(resource_owner_id, error_message)` - Permission checking
- `handle_service_result(result, success_message, success_redirect, error_redirect)` - Service response handling
- `save_uploaded_images(uploaded_files, upload_folder, subfolder)` - Image upload processing
- `delete_image_file(image_path, upload_folder)` - Image deletion
- `get_booking_display_status(booking)` - Computes "in_progress" status for bookings
- `categorize_bookings(bookings, section_filter)` - Splits bookings into upcoming/in_progress/previous/canceled
- `log_admin_action(admin_id, action, target_table, target_id, details)` - Admin action logging

### Query Builder (`src/utils/query_builder.py`)
Fluent API for dynamic SQL query construction:
```python
from src.utils.query_builder import QueryBuilder

qb = QueryBuilder('resources')
qb.add_condition('status = ?', 'active')
qb.add_like_filter('title', search_term)
qb.set_order_by('created_at', 'DESC')
qb.set_pagination(limit=20, offset=0)
query, params = qb.build()
```

### Configuration (`src/utils/config.py`)
Centralized environment-based configuration:
- `Config.validate()` - Validates required config on startup
- All config accessed via `Config.VARIABLE_NAME` (e.g., `Config.SECRET_KEY`)
- Never hardcode configuration values

### DateTime Utilities (`src/utils/datetime_utils.py`)
- `parse_datetime_aware(dt_string)` - Parse ISO datetime strings to timezone-aware datetime
- `format_datetime_est(value, format_type)` - Format datetime in EST timezone
- All datetimes stored in UTC, displayed in EST (configurable via `TIMEZONE` env var)

### Other Utilities
- `json_utils.py` - Safe JSON parsing (`safe_json_loads`, `safe_json_dumps`)
- `html_utils.py` - HTML sanitization for user input
- `logging_config.py` - Structured logging with file rotation
- `exceptions.py` - Custom exception classes (`DatabaseError`, `ValidationError`, etc.)
- `decorators.py` - Role-based access decorators (`@admin_required`, `@login_required`)

## Important Patterns

### Service Layer Pattern
Always return standardized responses from services:
```python
# Success response
return {'success': True, 'data': {'resource_id': 123, 'other_key': value}}

# Error response
return {'success': False, 'error': 'User-friendly error message'}
```

### Database Access Pattern
Always use context manager:
```python
from src.data_access.database import get_db_connection

with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
```
Never manually commit/rollback - context manager handles this automatically.

### Image Upload Pattern
Use controller helpers instead of duplicating image upload logic:
```python
from src.utils.controller_helpers import save_uploaded_images

uploaded_files = request.files.getlist('images')
image_paths = save_uploaded_images(uploaded_files, app.config['UPLOAD_FOLDER'], 'resources')
```

### Permission Checking Pattern
Use controller helpers for consistent permission checks:
```python
from src.utils.controller_helpers import check_resource_permission

has_permission, error_response = check_resource_permission(resource['owner_id'])
if not has_permission:
    return error_response
```

### Booking Time Validation
Bookings use timezone-aware datetimes (stored in UTC). The `booking_service.py` handles:
- Conflict detection across overlapping time ranges
- Operating hours validation (per-resource or global)
- Minimum/maximum duration enforcement
- Minimum advance booking time

### Message Threading
Messages are grouped by `thread_id` (deterministic based on resource + user pair). The `messaging_service.py`:
- Generates consistent `thread_id` using hash of sorted user IDs + resource ID
- Tracks read/unread status per user per thread in `thread_read` table
- Navbar displays unread message count via context processor in `app.py:129`

## Testing Strategy

**Test Organization:**
- `test_*_service.py` - Unit tests for service layer business logic
- `test_*_integration.py` - Integration tests with database
- `test_*_e2e.py` - End-to-end tests simulating user workflows
- `test_security.py` - Security-focused tests (XSS, SQL injection, auth bypass)

**Test Database:**
Tests use separate database (`test_*.db`) to avoid corrupting development data. Set `DATABASE_PATH` environment variable in tests.

## Configuration Management

All configuration via environment variables (`.env` file):
- **Required:** `SECRET_KEY`, `DATABASE_PATH`, `UPLOAD_FOLDER`
- **Optional:** See `.env.example` for full list with defaults
- `Config.validate()` runs on application startup to catch misconfigurations early

## Security Notes

- **Password Hashing:** Uses `bcrypt` (never store plaintext passwords)
- **SQL Injection Prevention:** Always use parameterized queries (`?` placeholders)
- **XSS Prevention:** All user input sanitized via `html_utils.sanitize_html()`
- **File Upload Security:** Validated extensions, unique filenames (UUID), secure_filename()
- **Session Security:** Flask-Login with secure session cookies
- **Role-Based Access:** Decorators enforce role requirements (`@admin_required`, `@staff_required`)
- **Soft Delete:** Users are soft-deleted (flagged as `deleted=1`) rather than hard-deleted

## AI Concierge Feature

The AI Concierge (`src/services/ai_concierge.py`) integrates Google Gemini API:
- Requires `GOOGLE_GEMINI_API_KEY` in `.env`
- Can be disabled via `ENABLE_AI_CONCIERGE=0`
- Natural language queries for resource search
- Controller: `ai_concierge_controller.py`, route: `/ai-concierge/chat`

## Common Gotchas

1. **Image Paths:** Always store relative paths in database (e.g., `resources/uuid.jpg`), never absolute paths
2. **Datetime Handling:** All datetimes in database are UTC; use `parse_datetime_aware()` and `format_datetime_est()` for conversions
3. **JSON Fields:** Resources.images and availability_rules are JSON-encoded strings; use `safe_json_loads()` to parse
4. **Cascade Deletes:** Be careful when deleting resources - related bookings/reviews/messages may need cleanup
5. **Operating Hours:** Resources can override global operating hours; check `is_24_hours` flag and resource-specific hours
6. **Thread Read Status:** When marking messages as read, update `thread_read` table, not individual message `read` flag
7. **Admin Logs:** All admin actions (feature, archive, delete user) should be logged via `log_admin_action()`

## Default Test Credentials

Sample database includes test accounts (see README.md):
- Admin: `admin@iu.edu` / `AdminUser1!`
- Staff: `staffuser@iu.edu` / `StaffUser1!`
- Student: `studentuser@iu.edu` / `StudentUser1!`

**NEVER use these in production!**
