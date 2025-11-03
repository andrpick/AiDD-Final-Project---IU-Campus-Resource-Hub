# Indiana University Campus Resource Hub - Setup and Completion Steps

This document provides a simple checklist of steps to set up and use the application.

## ✅ All Features Completed

The application is fully functional with all core features implemented:
- ✅ Project folder structure
- ✅ Database with sample/starter data included
- ✅ All service layer files (business logic)
- ✅ All controller files (Flask blueprints)
- ✅ All template files (HTML views)
- ✅ Main Flask application (`app.py`)
- ✅ Static files (CSS with IU branding)
- ✅ Image upload functionality (multiple images per resource)
- ✅ Admin user management modals
- ✅ Booking system with conflict detection
- ✅ Calendar export (Google Calendar, Outlook, iCal)
- ✅ AI Concierge chatbot with Google Gemini
- ✅ Messaging system
- ✅ Reviews and ratings
- ✅ Admin dashboard and booking management
- ✅ Test structure
- ✅ Configuration files (requirements.txt, README.md, .gitignore)

## 📋 Steps to Complete

### 1. Initial Setup

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
   
   **Note:** The database (`campus_resource_hub.db`) is included with the project and contains sample/starter data to help you get started quickly. The default admin account credentials are:
   - Email: `admin@iu.edu`
   - Password: `Admin123!`
   
   Additional sample users may be included in the database with various email addresses. Check the User Management page after logging in to see all available accounts.

### 2. Test Basic Functionality
1. **Run the application:**
   ```bash
   python app.py
   ```

2. **Access the application:**
   - Open `http://localhost:5000` in your browser
   - Try logging in with the admin account (included in sample data)
   - Register a new user account
   - Explore the sample resources and bookings
   - Create a test resource
   - Make a test booking

### 3. Environment Setup

#### A. AI Concierge Setup (Optional)
The AI Concierge uses Google Gemini for natural language resource queries:
1. Get a Google Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Add it to your `.env` file as `GOOGLE_GEMINI_API_KEY`
3. The chatbot will use a fallback search-based response if no API key is provided

#### B. Database Notes
- The database (`campus_resource_hub.db`) is included with the project and contains sample/starter data
- The database includes sample resources, users, bookings, and other data to help you get started
- All database migrations have been completed
- Migration scripts are archived in the `archive/` folder for reference
- The `init_db.py` script is available if you need to recreate the database from scratch

### 4. Key Features Overview

The application includes the following implemented features:

1. **Resource Management:**
   - Create, edit, and delete resources
   - Upload multiple images per resource
   - Optional capacity constraints
   - Featured resources for homepage
   - Resource archiving (admin-only)

2. **Booking System:**
   - Interactive month-view calendar for date selection
   - Day-view with drag-and-select time slot selection (8 AM - 10 PM)
   - Current time indicator on the current day
   - Automatic approval for available slots (no conflicts) - bookings are automatically approved when created
   - Simplified booking workflow: bookings are either 'approved', 'cancelled', or 'completed' (no pending/rejected statuses)
   - Conflict detection prevents double-booking
   - Calendar export to Google Calendar, Outlook, and iCal formats
   - Admin booking management with override capabilities (modify/cancel any booking)
   - Booking duration validation (minimum 30 minutes, maximum 8 hours)
   - Advance booking requirement (must be at least 1 hour in the future)
   - All times displayed in EST/EDT timezone

3. **User Features:**
   - User registration and authentication
   - Profile management
   - Multiple reviews per resource (users can review a resource multiple times)
   - Thread-based messaging system with resource-specific threading
   - Read/unread thread status tracking
   - Unread message notifications in navbar
   - Booking calendar integration with drag-and-select time selection
   - Calendar export (Google Calendar, Outlook, iCal)

4. **Admin Features:**
   - **User Management**:
     - Full user editing (edit name, email, password, role, department, profile image, suspension status)
     - Suspend/unsuspend users with reason
     - Change user roles (with self-demotion prevention)
     - Delete users (with cascade effects)
     - Streamlined dropdown menu interface for all user actions
   - **Resource Management**:
     - Comprehensive filtering options (status, category, featured status, location, owner, keyword search)
     - Resource archiving and unarchiving
     - Feature/unfeature resources for homepage
     - Edit any resource (admins can edit all resources)
     - Filter combinations preserved across pagination
   - **Booking Management**:
     - View all bookings with section filtering (upcoming, previous, canceled)
     - Filter by status, resource, and requester
     - Admin booking override capabilities
   - **Statistics Dashboard**:
     - Resource Statistics section with detailed analytics (bookings, reviews, ratings)
     - Filtering options (category, location, featured status)
     - Sorting options (by bookings, reviews, rating, title, category, location)
     - Table format display for easy comparison
     - Summary cards with breakdown statistics (users by role, resources by status, bookings by status, reviews by rating)
   - Admin action logging with comprehensive filtering and audit trail

5. **AI Concierge:**
   - Chatbot widget accessible from any page (bottom-right corner)
   - Google Gemini AI integration with read-only database access
   - Natural language resource queries with strict topic guardrails
   - Supports queries for:
     - Database statistics ("How many resources are there?")
     - Resource details ("Tell me about Merchants Bank Field")
     - Resource comparisons ("Compare Study Room A vs Study Room B")
     - Availability checks ("When is Resource X available?")
     - Category/location filtering ("Show me study rooms in the library")
     - Top-rated resources ("What are the best resources?")
     - Recently added resources ("What resources were recently added?")
   - Fallback to search-based responses if Gemini API unavailable

### 5. Testing the Application

1. **Create sample resources:**
   - Log in as admin or create a staff account
   - Create resources with multiple images
   - Test with and without capacity constraints

2. **Test bookings:**
   - Create bookings with different time slots
   - Test conflict detection (try booking overlapping times)
   - Export bookings to calendar
   - Test admin booking override

3. **Test messaging:**
   - Start conversations with other users via the "New Message" button
   - Test the "Message Owner" button on resource detail pages
   - Verify resource-specific threading (separate threads per resource)
   - Test read/unread thread status (mark as read/unread on messages index page)
   - Verify unread message count appears in navbar badge

4. **Test admin features:**
   - Edit users (change name, email, password, role, department, profile image, suspension status)
   - Suspend/unsuspend users
   - Change user roles
   - Test Resource Management filtering (status, category, featured, location, owner, keyword search)
   - Archive/unarchive resources
   - Feature/unfeature resources
   - View booking management with section and status filtering
   - Explore Resource Statistics with filtering and sorting

### 6. Testing Checklist

#### Manual Testing:
- [x] User registration and login
- [x] Resource creation, editing, deletion with multiple images
- [x] Resource image removal during editing (admin-only)
- [x] Optional capacity constraints (checkbox + input)
- [x] Featured resources toggle (admin-only)
- [x] Resource archiving (admin-only)
- [x] Booking creation with month/day calendar view
- [x] Drag-and-select time slot selection
- [x] Booking conflict detection and prevention
- [x] Automatic booking approval for available slots (simplified workflow - no pending/rejected statuses)
- [x] Booking calendar export (Google Calendar, Outlook, iCal)
- [x] Admin booking management and override
- [x] Review submission (multiple reviews per user per resource)
- [x] Thread-based messaging with resource-specific threading
- [x] Read/unread thread status tracking
- [x] Mark threads as read/unread
- [x] Unread message notifications in navbar
- [x] "Message Owner" button on resource pages
- [x] Advanced search and filtering
- [x] AI Concierge queries (statistics, resource details, availability, comparisons)
- [x] AI Concierge with Google Gemini integration
- [x] AI Concierge read-only database access

#### Security Features:
- [x] SQL injection prevention (parameterized queries)
- [x] XSS prevention (input sanitization)
- [x] Authorization checks (role-based access)
- [x] CSRF protection (Flask-WTF)
- [x] Password hashing (bcrypt)

### 7. Deployment Preparation

1. **Environment variables:**
   - Set proper `SECRET_KEY` in production
   - Configure database path
   - Set upload folder permissions

2. **Database:**
   - Consider migrating to PostgreSQL for production
   - Set up database backups

3. **Static files:**
   - Consider using CDN for Bootstrap/CSS
   - Optimize images

4. **Security:**
   - Change default admin password
   - Enable HTTPS
   - Configure secure cookies
   - Set up rate limiting

## 🎯 Quick Reference

### Default Admin Account
- **Email:** admin@iu.edu
- **Password:** Admin123!
- **⚠️ CHANGE THIS IN PRODUCTION!**

**Note:** Additional sample users may be included in the database with various email addresses. You can view all users in the Admin Dashboard > User Management section.

### Key Files to Review/Edit
- `app.py` - Main Flask application
- `src/controllers/` - Route handlers (add image upload here)
- `src/views/admin/users.html` - Add modals here
- `src/services/` - Business logic (mostly complete)
- `src/static/css/main.css` - Customize styling if needed

### Common Issues & Solutions

**Issue:** Database errors on first run
- **Solution:** Ensure the `campus_resource_hub.db` file exists in the project root. If it's missing, you can recreate it by running `python init_db.py`

**Issue:** Virtual environment not activating
- **Solution:** On Windows, you may need to run `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` in PowerShell before activating the virtual environment

**Issue:** Images not displaying
- **Solution:** Ensure the `uploads/` folder exists and has proper permissions

**Issue:** Admin modals not working
- **Solution:** Ensure Bootstrap JavaScript is loaded correctly

**Issue:** Booking conflicts not detected
- **Solution:** Check `src/services/booking_service.py` conflict detection logic

## 📝 Notes

- ✅ All core functionality is fully implemented
- ✅ All 52 tests passing (100% pass rate)
- ✅ Templates use Bootstrap 5 with Indiana University colors (crimson #990000, cream #EEEDEB)
- ✅ Database uses SQLite (easy to switch to PostgreSQL later)
- ✅ Database is included with sample/starter data - no initialization needed
- ✅ All validation and business logic is complete
- ✅ Migration scripts and outdated documentation archived in `archive/` folder
- ✅ Calendar export supports Google Calendar, Outlook, and iCal formats
- ✅ AI Concierge uses Google Gemini API (with fallback to search-based responses)
- ✅ Thread-based messaging with resource-specific threading
- ✅ Read/unread message tracking with navbar notifications
- ✅ Admin user editing functionality (full user profile management)
- ✅ Simplified booking workflow (automatic approval, no pending/rejected statuses)
- ✅ Enhanced Resource Statistics section with filtering and sorting
- ✅ Comprehensive Resource Management filtering (status, category, featured, location, owner, keyword search)
- ✅ Admin dashboard summary cards with breakdown statistics displayed in table format

## 🧪 Testing

The application includes a comprehensive test suite:

**Test Coverage:**
- ✅ 52 tests total (100% passing)
- ✅ Unit tests: Booking logic, data access layer, validation
- ✅ Integration tests: Authentication flows, booking workflows
- ✅ End-to-end tests: Complete user journeys (search → book → verify)
- ✅ Security tests: SQL injection prevention, XSS protection, input sanitization

**Running Tests:**
```bash
# Activate virtual environment (if using one)
.\.venv\Scripts\Activate.ps1  # Windows PowerShell
# or
source .venv/bin/activate  # Linux/Mac

# Quick way - use the test runner script
python tests/run_tests.py

# Or use pytest directly
python -m pytest tests/ -v

# Run specific test file
python -m pytest tests/test_booking_service.py -v

# Run with coverage report
python -m pytest tests/ --cov=src --cov-report=html
```

**Test Files:**
- `tests/test_booking_service.py` - Booking logic unit tests (16 tests)
- `tests/test_booking_e2e.py` - End-to-end booking tests (5 tests)
- `tests/test_data_access.py` - Data access layer tests (11 tests)
- `tests/test_auth_integration.py` - Authentication integration tests (8 tests)
- `tests/test_app_integration.py` - Application integration tests (2 tests)
- `tests/test_security.py` - Security tests (8 tests)
- `tests/ai_eval/test_ai_concierge.py` - AI Concierge tests (2 tests)

**Current Status:** ✅ All 52 tests passing

## 🔧 Archive Folder

The `archive/` folder contains migration scripts and outdated documentation:
- **Migration scripts** (6 files):
  - `migrate_remove_capacity_limit.py` - Removed 500 capacity limit
  - `migrate_add_featured.py` - Added featured column to resources
  - `migrate_allow_multiple_reviews.py` - Removed unique constraint on reviews
  - `migrate_make_capacity_optional.py` - Made capacity nullable
  - `migrate_add_resource_id_to_messages.py` - Added resource_id to messages
  - `migrate_add_thread_read_tracking.py` - Added thread_read table
- **Utility scripts:**
  - `clear_old_messages.py` - Utility script (no longer needed)
- **Old templates:**
  - `views/ai_concierge/concierge.html` - Legacy AI concierge page
  - `views/resources/index.html` - Legacy resources index page
- **Outdated documentation:**
  - `MISSING_COMPONENTS.md` - Outdated component tracking
  - `tests/FAILING_TESTS_ANALYSIS.md` - Historical test analysis (all tests now pass)
  - `ARCHIVE_REVIEW.md` - Archive review document

These files are kept for reference but are no longer needed as the database is included with the project. The `init_db.py` script is available if you need to recreate the database from scratch.

---

**The application is ready for use!** 🚀

