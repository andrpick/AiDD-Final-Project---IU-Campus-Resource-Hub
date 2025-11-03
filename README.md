# Indiana University Campus Resource Hub

A full-stack web application for managing and booking campus resources including study rooms, AV equipment, lab instruments, event spaces, and tutoring services.

## Setup Instructions

1. **Create a virtual environment:**
   ```bash
   # Windows PowerShell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   
   # Windows Command Prompt
   python -m venv .venv
   .venv\Scripts\activate.bat
   
   # Linux/Mac
   python3 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** in the project root:
   ```
   SECRET_KEY=your-secret-key-change-this
   DATABASE_PATH=campus_resource_hub.db
   UPLOAD_FOLDER=uploads/
   GOOGLE_GEMINI_API_KEY=your-api-key-here (optional, for AI Concierge)
   ```
   
   **Note:** The database (`campus_resource_hub.db`) is included with the project and contains sample/starter data to help you get started quickly.

4. **Run the application:**
   ```bash
   python app.py
   ```

The application will be available at `http://localhost:5000`

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
- `src/controllers/` - Flask blueprints (route handlers)
- `src/models/` - Data models
- `src/services/` - Business logic layer
- `src/data_access/` - Database access layer
- `src/views/` - Jinja2 templates
- `src/static/` - Static files (CSS, JS, images)
- `tests/` - Test suite (52 tests, 100% passing)
- `uploads/` - User-uploaded files
- `archive/` - Archived migration scripts and outdated documentation

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
- **Utilities**: Python-dateutil (timezone handling), bcrypt (password hashing)
- **Styling**: Custom CSS with Indiana University branding (Crimson #990000, Cream #EEEDEB)

## Testing

The application includes a comprehensive test suite with 52 tests covering:
- Unit tests for booking logic and data access
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

**Current Status:** ✅ All 52 tests passing (100% pass rate)

## Environment Variables

Create a `.env` file in the project root with:

```
SECRET_KEY=your-secret-key-here
DATABASE_PATH=campus_resource_hub.db
UPLOAD_FOLDER=uploads/
GOOGLE_GEMINI_API_KEY=your-gemini-api-key (optional, for AI Concierge)
```

**Note:** The database (`campus_resource_hub.db`) is included with sample/starter data. No database initialization is required. The `init_db.py` script is available if you need to recreate the database from scratch.

