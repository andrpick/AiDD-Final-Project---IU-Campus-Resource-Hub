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

1. **Create a virtual environment**
   - VS Code shortcut: `View` → `Command Palette…` → `Python: Create Environment` → choose **Venv** and select **requirements.txt**.
   - Manual commands:
     ```bash
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1    # Windows PowerShell
     # or
     source .venv/bin/activate       # macOS / Linux
     ```
2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Create a `.env` file** in the project root:
   ```bash
   # Copy the template
   cp .env.example .env
   ```
   
   Then edit `.env` and update at minimum:
   - `SECRET_KEY` - Generate a secure random key: `python -c "import secrets; print(secrets.token_hex(32))"`
   - Other values as needed
   
   See `.env.example` for all available configuration options including:
   - Flask settings (host, port, debug mode)
   - Logging configuration
   - Booking system settings (operating hours, timezone, duration limits)
   - Feature flags (AI Concierge, registration)
   - Production settings
   
   **Note:** The database (`campus_resource_hub.db`) is included with the project and contains sample/starter data to help you get started quickly. The default user accounts are:
   
   **Admin User:**
   - Email: `admin@iu.edu`
   - Password: `AdminUser1!`
   
   **Staff User:**
   - Email: `staff@iu.edu`
   - Password: `StaffUser1!`
   
   **Student User:**
   - Email: `student@iu.edu`
   - Password: `StudentUser1!`
   
   **⚠️ SECURITY WARNING:** These are default test credentials for development and testing purposes only. **You MUST change all default passwords immediately after first login in production environments.** Never use default credentials in production!
   
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
- All database schema changes have been completed and are included in `init_db.py`
- The `init_db.py` script is available if you need to recreate the database from scratch

### 4. Key Features Overview

The application includes comprehensive features for resource management, booking, messaging, reviews, and administration. 

**Core Features:**
- User Authentication & Authorization (role-based access, CSRF protection, secure password hashing)
- Resource Management (CRUD, multiple images, resource-specific operating hours, archiving)
- Booking System (calendar view, conflict detection, automatic approval, status tracking, calendar export, email notifications)
- Messaging System (thread-based messaging, read/unread tracking, notifications)
- Reviews & Ratings (multiple reviews per user per resource)
- AI Concierge "Crimson" (Google Gemini integration, natural language queries, context-aware responses)
- Admin Dashboard (user/resource/booking management, statistics, action logging)
- Advanced Search & Filtering (keyword, category, location, capacity, availability filtering)

For a high-level overview, see [README.md](README.md#features). For complete technical specifications and business rules, see [docs/context/PRD_COMPLETE.md](docs/context/PRD_COMPLETE.md). For API endpoint documentation, see [API.md](API.md).

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
   - Test Resource Management filtering with filter modals (status, category, featured, location, owner, keyword search, operating hours)
   - Test User Management filtering with filter modals (search, role, status, show deleted)
   - Test Booking Management filtering with filter modals (status, resource, requester)
   - Test Admin Logs filtering with filter modals (admin, action, target table)
   - Test Resource Statistics filtering with filter modals (category, location, featured, sort by)
   - Archive/unarchive resources
   - Feature/unfeature resources
   - View booking management with section and status filtering (including "In Progress" status)
   - Explore Resource Statistics with filtering and sorting
   - Test "Clear All Filters" functionality on all admin pages

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
- [x] Review submission (multiple reviews per user per resource - one review per completed booking)
- [x] Profile image upload with cropping (all user types)
- [x] Booking status "In Progress" (computed status for active bookings)
- [x] Filter modals across admin pages (User Management, Resource Management, Booking Management, Admin Logs, Resource Statistics)
- [x] Clear all filters functionality
- [x] Past date/time validation for availability filtering
- [x] AI Concierge "Crimson" with markdown rendering and persistent chat history
- [x] Adaptive message bubble sizing
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
- [x] CSRF protection (Flask-WTF) - All forms protected with CSRF tokens
- [x] Password hashing (bcrypt)

For detailed security requirements and implementation, see [docs/context/PRD_COMPLETE.md](docs/context/PRD_COMPLETE.md#9-security-requirements).

### 7. Deployment Preparation

1. **Environment variables:**
   - Copy `.env.example` to `.env`
   - Set proper `SECRET_KEY` in production (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
   - Configure database path
   - Set upload folder permissions
   - Set `PRODUCTION=1` and `FLASK_DEBUG=0` for production
   - Configure all booking system settings as needed
   - See `.env.example` for complete documentation and all available options

2. **Database:**
   - **Current:** SQLite (suitable for development and class projects)
   - **Production Recommendation:** Migrate to PostgreSQL or MySQL
     - Better concurrent access and multi-server support
     - Connection pooling capabilities
     - Built-in replication and backup features
     - Improved performance for larger datasets
   - Set up automated database backups (daily/hourly)
   - Implement database connection pooling
   - Consider read replicas for read-heavy workloads

3. **File Storage:**
   - **Current:** Local filesystem (`uploads/` directory)
   - **Production Recommendation:** Migrate to cloud object storage
     - **AWS S3**, **Google Cloud Storage**, or **Azure Blob Storage**
     - Enables horizontal scaling across multiple servers
     - CDN integration for faster image delivery
     - Automatic backup and redundancy
     - Implement image optimization/compression on upload
     - Generate thumbnails for different use cases
   - If keeping local storage: ensure proper backup procedures

4. **Static Files:**
   - Consider using CDN for Bootstrap/CSS and static assets
   - Optimize and minify CSS/JavaScript
   - Implement browser caching headers

5. **Application Server:**
   - **Current:** Flask development server (single-threaded)
   - **Production Recommendation:** Use production WSGI server
     - **Gunicorn** or **uWSGI** with multiple worker processes
     - **Nginx** as reverse proxy and load balancer
     - Deploy multiple application instances for high availability
     - Consider containerization (Docker) for consistent deployments
     - Use process managers (systemd, supervisord) for service management

6. **Session Management:**
   - **Current:** Flask session cookies (server-side storage)
   - **Production Recommendation:** External session storage
     - **Redis** or **Memcached** for session storage
     - Enables session sharing across multiple application servers
     - Better performance and scalability

7. **Caching:**
   - **Recommendation:** Implement caching layers
     - **Redis** for frequently accessed data (resource listings, user sessions)
     - Cache database query results where appropriate
     - Implement cache invalidation strategies
     - CDN caching for static assets

8. **Monitoring & Logging:**
   - **Recommendation:** Implement comprehensive monitoring
     - Application performance monitoring (APM) tools
     - Error tracking services (Sentry, Rollbar)
     - Log aggregation and analysis (ELK stack, CloudWatch)
     - Health check endpoints for load balancers
     - Database query performance monitoring
     - Set up alerts for critical errors and performance issues

9. **Security:**
   - **CRITICAL:** Change all default passwords (admin, staff, student accounts) before production deployment
   - **CRITICAL:** Generate a secure `SECRET_KEY` (never use the default placeholder)
   - Enable HTTPS
   - Configure secure cookies
   - Set up rate limiting
   - Ensure `SECRET_KEY` is strong and unique (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
   - Never commit `.env` files to version control
   - Store API keys securely in `.env` file (never in code)

10. **Performance Optimization:**
    - Database query optimization and proper indexing
    - Implement database connection pooling
    - Use async/background tasks for heavy operations (Celery + Redis)
    - Optimize static asset delivery (minification, compression)
    - Implement API rate limiting (Flask-Limiter)
    - Consider implementing database read replicas for read-heavy workloads

11. **Backup & Disaster Recovery:**
    - Automated database backups (daily/hourly)
    - File storage backups (if using local storage)
    - Test restore procedures regularly
    - Document disaster recovery procedures
    - Consider geographic redundancy for critical data

12. **Logging:**
    - Configure log directory and rotation
    - Set up log monitoring/alerting
    - Review logs regularly for errors
    - Implement structured logging for better analysis

## 🎯 Quick Reference

### Default User Accounts

See [README.md](README.md#default-admin-account) for default credentials and security warnings.

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
- ✅ All 139 tests passing (100% pass rate)
- ✅ Templates use Bootstrap 5 with Indiana University colors (crimson #990000, white)
- ✅ Clean, modern UI design with subtle shadows and hover effects
- ✅ Database uses SQLite (easy to switch to PostgreSQL later)
- ✅ Database is included with sample/starter data - no initialization needed
- ✅ All validation and business logic is complete
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

The application includes a comprehensive test suite with **139 tests** (100% pass rate). For testing information, see [README.md](README.md#testing).

**Quick Start:**
```bash
python tests/run_tests.py
```

## 🆕 Recent Improvements

### Code Refactoring (Completed)
- ✅ **Utility Modules**: Centralized utilities for datetime, JSON, HTML processing (`src/utils/`)
- ✅ **Error Handling**: Comprehensive error handling with custom exceptions and structured logging
- ✅ **Configuration System**: Environment variable-based configuration with validation (`src/utils/config.py`)
- ✅ **Calendar Service**: Extracted calendar processing logic into dedicated service (`src/services/calendar_service.py`)
- ✅ **Logging**: Production-ready logging with file rotation and error tracking (`src/utils/logging_config.py`)
- ✅ **Controller Helpers** (`src/utils/controller_helpers.py`): Reusable functions for permission checks, image upload handling, and service result processing
- ✅ **Query Builder** (`src/utils/query_builder.py`): Fluent API for building dynamic SQL queries programmatically
- ✅ **Reduced Code Duplication**: Image upload logic consolidated from ~50 duplicated lines to reusable functions
- ✅ **Standardized Patterns**: Consistent permission checks and error handling across controllers

### UI & UX Improvements (Completed)
- ✅ **UI Standardization**: Standardized all filter/sort boxes across the web app for consistent user experience
- ✅ **Form Input Consistency**: All form inputs use `form-control-sm` and `form-select-sm` for uniform heights
- ✅ **Button Standardization**: All Apply and Reset buttons have consistent height (`py-2`), width (side-by-side use `flex-fill`, separate columns use `w-100`), and font size (`0.875rem`)
- ✅ **Label Standardization**: All labels use consistent margin (`mb-1`), font size (`0.875rem`), and font weight (`fw-semibold`)
- ✅ **Visual Consistency**: Uniform styling across all filter/sort interfaces for improved usability and professional appearance

### New Features Added
- ✅ **Centralized Configuration**: `src/utils/config.py` for all environment variables
- ✅ **Custom Exceptions**: `src/utils/exceptions.py` for better error categorization
- ✅ **Structured Logging**: `src/utils/logging_config.py` with file rotation
- ✅ **Calendar Service**: `src/services/calendar_service.py` for booking calendar logic
- ✅ **Environment Variables**: Complete `.env.example` template with all options
- ✅ **Decorators**: `src/utils/decorators.py` for common decorators (admin_required, etc.)
- ✅ **Profile Image Upload with Cropping**: All user types can upload profile pictures with 1:1 aspect ratio cropping
- ✅ **Filter Modals**: Consistent filter modal pattern across all admin pages (User Management, Resource Management, Booking Management, Admin Logs, Resource Statistics)
- ✅ **Booking Status "In Progress"**: Computed status for currently active bookings
- ✅ **Multiple Reviews per Completed Booking**: Users can leave one review per completed booking for a resource
- ✅ **AI Assistant "Crimson"**: Named AI assistant with markdown rendering and persistent chat history
- ✅ **Past Date/Time Validation**: Availability filtering prevents selection of past dates/times
- ✅ **Clear All Filters**: One-click reset of all active filters across all pages
- ✅ **Adaptive Message Bubble Sizing**: Message bubbles adapt to content length for optimal display

### Documentation Updates
- ✅ **Environment Variables**: See `.env.example` and README.md Environment Variables section
- ✅ **README**: Updated with comprehensive environment variable documentation and code quality improvements

---

**The application is ready for use!** 🚀

