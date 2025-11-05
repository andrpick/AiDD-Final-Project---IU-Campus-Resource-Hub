# Indiana University Campus Resource Hub

A full-stack web application for managing and booking campus resources including study rooms, AV equipment, lab instruments, event spaces, and tutoring services.

## Quick Start

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env`** and set at minimum:
   - `SECRET_KEY` - Generate a secure key: `python -c "import secrets; print(secrets.token_hex(32))"`

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python app.py
   ```

The application will be available at `http://localhost:5000`

For detailed setup instructions, see [SETUP_STEPS.md](SETUP_STEPS.md).  
For detailed environment variable documentation, see `.env.example` and the Environment Variables section below.

## Default Admin Account

The database includes sample/starter data with a default admin account:
- **Email:** admin@iu.edu  
- **Password:** Admin123!

**⚠️ IMPORTANT:** Change the default admin password immediately after first login in production!

**Note:** The sample database may include additional test users with various email addresses. Check the User Management page after logging in to see all available accounts.

## Project Structure

- `app.py` - Flask application entry point
- `campus_resource_hub.db` - SQLite database with sample/starter data included
- `init_db.py` - Database initialization script (available if you need to recreate the database from scratch)
- `.env.example` - Environment variable template (copy to `.env` and customize)
- `src/controllers/` - Flask blueprints (route handlers)
- `src/models/` - Data models
- `src/services/` - Business logic layer
  - `calendar_service.py` - Calendar processing utilities
- `src/data_access/` - Database access layer
- `src/utils/` - Utility modules
  - `config.py` - Centralized configuration management
  - `exceptions.py` - Custom exception classes
  - `logging_config.py` - Logging configuration
  - `datetime_utils.py` - Datetime utilities
  - `json_utils.py` - JSON parsing utilities
  - `html_utils.py` - HTML sanitization utilities
  - `decorators.py` - Common decorators
  - `controller_helpers.py` - Reusable controller helper functions (permission checks, image handling)
  - `query_builder.py` - Fluent SQL query builder for dynamic queries
- `src/views/` - Jinja2 templates
- `src/static/` - Static files (CSS, JS, images)
- `tests/` - Test suite (139 tests, 100% passing)
- `uploads/` - User-uploaded files
- `logs/` - Application logs (auto-generated)
- `archive/` - Archived migration scripts, outdated documentation, and generated artifacts

## Features

### Core Features
- **User Authentication & Authorization**: Role-based access control (Student, Staff, Admin) with secure password hashing
- **Resource Management**: Full CRUD operations with multiple image uploads, optional capacity constraints, and admin-only archiving
- **Advanced Search & Filtering**: Keyword search, category filtering, location filtering, and capacity-based search
- **Booking System**: 
  - Interactive month/day calendar view with drag-and-select time selection
  - Automatic approval for available time slots (no manual approval needed)
  - Booking statuses: approved, cancelled, completed (simplified workflow)
  - Conflict detection and validation (prevents double-booking)
  - Calendar export to Google Calendar, Outlook, and iCal formats
  - Admin booking management with override capabilities
- **Messaging System**:
  - Thread-based messaging with resource-specific threading (separate threads per resource)
  - Thread-level read/unread status tracking
  - Unread message notifications in navbar
  - Mark threads as read/unread functionality
  - "Message Owner" button on resource detail pages
- **Reviews & Ratings**: Multiple reviews per user per resource with star ratings
- **AI Concierge**: 
  - Chatbot widget accessible from any page
  - Google Gemini AI integration
  - Natural language resource queries with read-only database access
  - Supports queries for statistics, resource details, availability, comparisons, and recommendations
- **Featured Resources**: Admin can feature resources for homepage display
- **Admin Dashboard**: Comprehensive statistics, user management, resource management, booking management, and action logging
  - **User Management**: Full user editing capabilities (edit name, email, password, role, department, profile image, suspension status)
  - **Resource Management**: Comprehensive filtering and management (filter by status, category, featured status, location, owner, and keyword search)
  - **Resource Statistics**: Detailed resource analytics with filtering and sorting options
  - **UI Improvements**: Streamlined dropdown menus for admin actions, table-based statistics display

## Technology Stack

- **Backend**: Flask 3.0.0+, SQLite (development), PostgreSQL (production-ready)
- **Frontend**: Bootstrap 5, Jinja2 templating, JavaScript (ES6+)
- **AI Integration**: Google Gemini API for natural language resource queries
- **Utilities**: 
  - Python-dateutil (timezone handling)
  - bcrypt (password hashing)
  - python-dotenv (environment variable management)
  - Custom utility modules for datetime, JSON, HTML processing
- **Configuration**: Environment variable-based configuration system
- **Logging**: Structured logging with file rotation
- **Styling**: Custom CSS with Indiana University branding (Crimson #990000, White)

## Testing

The application includes a comprehensive test suite with 139 tests covering:
- Unit tests for booking logic, data access layer, controller helpers, and query builder
- Integration tests for authentication and booking flows
- End-to-end tests for complete user workflows
- Security tests for SQL injection and XSS prevention

Run tests:
```bash
# Quick way - use the test runner script
python tests/run_tests.py

# Or use pytest directly
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_booking_service.py -v

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html
```

**Current Status:** ✅ All 139 tests passing (100% pass rate)

## Code Quality & Refactoring

The codebase has been refactored to improve maintainability and reduce duplication:

- **Controller Helpers** (`src/utils/controller_helpers.py`): Centralized functions for permission checking, image upload handling, and service result processing
- **Query Builder** (`src/utils/query_builder.py`): Fluent API for building dynamic SQL queries programmatically
- **Reduced Code Duplication**: Image upload logic consolidated from ~50 duplicated lines to reusable functions
- **Standardized Patterns**: Consistent permission checks and error handling across controllers

For detailed migration guides and examples, see the refactoring documentation in `archive/REFACTORING_SUMMARY.md`.

## Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

### Required Variables

```env
# Flask secret key for session management (CHANGE THIS IN PRODUCTION!)
# Generate a secure random key: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=your-secret-key-change-this

# Database file path (SQLite)
DATABASE_PATH=campus_resource_hub.db

# Upload folder for user-uploaded files
UPLOAD_FOLDER=uploads/
```

### Optional Variables

#### Application Settings
```env
# Flask debug mode (set to '1' to enable - NEVER enable in production!)
FLASK_DEBUG=0

# Flask host (default: 0.0.0.0)
FLASK_HOST=0.0.0.0

# Flask port (default: 5000)
FLASK_PORT=5000

# Maximum file upload size in bytes (default: 16MB = 16777216)
MAX_UPLOAD_SIZE=16777216
```

#### Logging Configuration
```env
# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL (default: INFO)
# If FLASK_DEBUG=1, this is automatically set to DEBUG
LOG_LEVEL=INFO

# Log directory (default: logs/)
LOG_DIR=logs/
```

#### AI Concierge Configuration
```env
# Google Gemini API key (optional, for AI Concierge feature)
# Get your API key from: https://makersuite.google.com/app/apikey
GOOGLE_GEMINI_API_KEY=your-api-key-here

# Enable AI Concierge feature (set to '1' to enable, requires GOOGLE_GEMINI_API_KEY)
ENABLE_AI_CONCIERGE=1
```

#### Booking System Configuration
```env
# Timezone for displaying dates/times (default: America/New_York)
# Use IANA timezone names: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones
TIMEZONE=America/New_York

# Operating hours start hour (24-hour format, default: 8)
BOOKING_OPERATING_HOURS_START=8

# Operating hours end hour (24-hour format, default: 22)
BOOKING_OPERATING_HOURS_END=22

# Minimum advance booking time in hours (default: 1)
BOOKING_MIN_ADVANCE_HOURS=1

# Minimum booking duration in minutes (default: 30)
BOOKING_MIN_DURATION_MINUTES=30

# Maximum booking duration in hours (default: 8)
BOOKING_MAX_DURATION_HOURS=8
```

#### Feature Flags
```env
# Enable user registration (set to '0' to disable registration)
ENABLE_REGISTRATION=1

# Production mode (set to '1' for production)
PRODUCTION=0
```

### Quick Start

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and update at minimum:
   - `SECRET_KEY` - Generate a secure random key
   - Other values as needed

3. For production, set:
   ```env
   PRODUCTION=1
   FLASK_DEBUG=0
   SECRET_KEY=<generate-secure-random-key>
   ```

**Note:** The database (`campus_resource_hub.db`) is included with sample/starter data. No database initialization is required. The `init_db.py` script is available if you need to recreate the database from scratch.

