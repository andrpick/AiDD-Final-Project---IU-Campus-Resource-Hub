# Indiana University Campus Resource Hub

A full-stack web application for managing and booking campus resources including study rooms, AV equipment, lab instruments, event spaces, and tutoring services.

## Quick Start

1. **Create a virtual environment**
   - VS Code shortcut: `View` → `Command Palette…` → `Python: Create Environment` → choose **Venv** and select **requirements.txt**.
   - Manual commands:
     ```bash
     python -m venv .venv
     .\.venv\Scripts\Activate.ps1    # Windows PowerShell
     # or
     source .venv/bin/activate       # macOS / Linux
     ```
2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure environment variables**
   ```bash
   cp .env.example .env   # use `copy` on Windows
   ```
   Review the new `.env` file end-to-end, update `SECRET_KEY`, and adjust any feature toggles you plan to use.
4. **Run the application**
   ```bash
   python app.py
   ```
   Visit `http://localhost:5000` to start exploring.

Need more detail? The streamlined checklist lives in [SETUP_STEPS.md](SETUP_STEPS.md).

## Default Admin Account

The database includes sample/starter data with default accounts:

### Admin User
- **Email:** admin@iu.edu  
- **Password:** AdminUser1!

### Staff User
- **Email:** staffuser@iu.edu
- **Password:** StaffUser1!

### Student User
- **Email:** studentuser@iu.edu
- **Password:** StudentUser1!

**⚠️ SECURITY WARNING:** These are default test credentials for development and testing purposes only. **You MUST change all default passwords immediately after first login in production environments.** Never use default credentials in production!

**Note:** The sample database may include additional test users with various email addresses. Check the User Management page after logging in to see all available accounts.

## Security Considerations

**⚠️ IMPORTANT SECURITY NOTES:**

1. **Default Credentials**: The application includes default test accounts with known passwords. These are for development and testing only. **You MUST change all default passwords before deploying to production.**

2. **Secret Key**: The default `SECRET_KEY` in `.env.example` is a placeholder. **You MUST generate a secure random key for production** using:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **Environment Variables**: Never commit `.env` files to version control. The `.env.example` file is a template only and contains no actual secrets.

4. **Production Deployment**: 
   - Set `PRODUCTION=1` and `FLASK_DEBUG=0` in your `.env` file
   - Use HTTPS in production
   - Configure secure session cookies
   - Set up proper database backups
   - Review and update all default credentials

5. **API Keys**: If using the AI Concierge feature, store your `GOOGLE_GEMINI_API_KEY` securely in your `.env` file (never commit it).

For more detailed security information, see the [SETUP_STEPS.md](SETUP_STEPS.md) Security section.

## Production Deployment & Scalability Considerations

**Note:** This application is designed for class project demonstration. For production deployment, consider the following scalability recommendations:

### Database Migration
- **Current:** SQLite (file-based, single-server)
- **Production Recommendation:** Migrate to PostgreSQL, MySQL, or another relational database
  - Better concurrent access handling
  - Supports multiple application servers
  - Built-in replication and backup features
  - Better performance for larger datasets
  - Connection pooling support

### File Storage
- **Current:** Local filesystem storage (`uploads/` directory)
- **Production Recommendation:** Migrate to cloud object storage
  - **AWS S3**, **Google Cloud Storage**, or **Azure Blob Storage**
  - Enables horizontal scaling across multiple servers
  - Built-in CDN integration for faster image delivery
  - Automatic backup and redundancy
  - Cost-effective pay-as-you-go pricing
  - Consider implementing image optimization/compression on upload
  - Generate thumbnails/variants for different use cases

### Session Management
- **Current:** Flask session cookies (server-side storage)
- **Production Recommendation:** Use external session storage
  - **Redis** or **Memcached** for session storage
  - Enables session sharing across multiple application servers
  - Better performance for high-traffic scenarios
  - Supports session expiration and cleanup

### Caching Strategy
- **Recommendation:** Implement caching layers
  - **Redis** for frequently accessed data (resource listings, user sessions)
  - Cache database query results where appropriate
  - Implement cache invalidation strategies
  - Consider CDN caching for static assets

### Application Server Scaling
- **Current:** Single Flask development server
- **Production Recommendation:** Use production WSGI server
  - **Gunicorn** or **uWSGI** with multiple workers
  - **Nginx** as reverse proxy and load balancer
  - Deploy multiple application instances behind load balancer
  - Consider containerization (Docker) for consistent deployments

### Monitoring & Logging
- **Recommendation:** Implement comprehensive monitoring
  - Application performance monitoring (APM) tools
  - Error tracking services (Sentry, Rollbar)
  - Log aggregation (ELK stack, CloudWatch, etc.)
  - Health check endpoints for load balancers
  - Database query performance monitoring

### Security Enhancements
- **Recommendation:** Additional security measures
  - Rate limiting (Flask-Limiter) to prevent abuse
  - DDoS protection via CDN or cloud provider
  - Regular security audits and dependency updates
  - Implement Content Security Policy (CSP) headers
  - Use HTTPS with proper certificate management

### Performance Optimization
- **Recommendation:** Optimize for production workloads
  - Database query optimization and indexing
  - Implement database connection pooling
  - Use async/background tasks for heavy operations (Celery + Redis)
  - Optimize static asset delivery (minification, compression)
  - Consider implementing API rate limiting

### Backup & Disaster Recovery
- **Recommendation:** Implement backup strategies
  - Automated database backups (daily/hourly)
  - File storage backups (if using local storage)
  - Test restore procedures regularly
  - Document disaster recovery procedures

For detailed deployment instructions and scalability recommendations, see [SETUP_STEPS.md](SETUP_STEPS.md#7-deployment-preparation).

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
- `docs/wireframes/` - Wireframe images for key pages (Homepage, Resource Listing, Resource Detail, User Dashboard, Messaging Interface)

## Features

The application includes the following core features:

- **User Authentication & Authorization**: Role-based access control (Student, Staff, Admin) with secure password hashing and profile image upload with cropping
- **Resource Management**: Full CRUD operations with multiple image uploads, optional capacity constraints, resource-specific operating hours (with 24-hour operation option), and admin-only archiving
- **Advanced Search & Filtering**: Keyword search, category filtering, location filtering, capacity-based search, availability date/time filtering (with past date/time validation), and clear all filters functionality
- **Booking System**: Interactive calendar view with drag-and-select time selection (12 AM - 11:59 PM), automatic approval, conflict detection, booking status tracking (including "In Progress" status), and calendar export (Google Calendar, Outlook, iCal)
- **Messaging System**: Thread-based messaging with resource-specific threading, read/unread status tracking, navbar notifications, and adaptive message bubble sizing
- **Reviews & Ratings**: Multiple reviews per user per resource (one review per completed booking) with star ratings
- **AI Concierge "Crimson"**: Chatbot widget with Google Gemini AI integration for natural language resource queries, markdown rendering in responses, and persistent chat history across page navigations
- **Admin Dashboard**: Comprehensive statistics, user management (including soft delete), resource management with filter modals, booking management with filter modals, and action logging with filter modals

For detailed feature descriptions, see [SETUP_STEPS.md](SETUP_STEPS.md#4-key-features-overview). For complete technical specifications, see [docs/context/PRD_COMPLETE.md](docs/context/PRD_COMPLETE.md).

## Technology Stack

- **Backend**: Flask 3.0.0+, SQLite (development), PostgreSQL (production-ready)
- **Frontend**: Bootstrap 5, Jinja2 templating, JavaScript (ES6+)
- **AI Integration**: Google Gemini API for natural language resource queries (AI assistant named "Crimson" with markdown rendering and persistent chat history)
- **Utilities**: 
  - Python-dateutil (timezone handling)
  - bcrypt (password hashing)
  - python-dotenv (environment variable management)
  - Custom utility modules for datetime, JSON, HTML processing
- **Configuration**: Environment variable-based configuration system
- **Logging**: Structured logging with file rotation
- **Styling**: Custom CSS with Indiana University branding (Crimson #990000, White)
  - Clean, modern design with Bootstrap 5 framework
  - **Standardized Shadow Utility Classes**: Consistent shadow effects across all pages
    - `.shadow-standard`: `0 4px 12px rgba(0,0,0,0.15)` - Used for cards and general elements
    - `.shadow-table`: `0 4px 12px rgba(0,0,0,0.15)` - Used for tables
    - `.shadow-inner`: `0 1px 3px rgba(0,0,0,0.1)` - Used for inner elements (dashboard stat boxes)
  - **Responsive Design**: Mobile-first approach with comprehensive breakpoints
    - Mobile (max-width: 767.98px): Time picker, message thread, chatbot widget, tables, filter/sort boxes
    - Tablet (max-width: 991.98px): Weekly calendar, time picker, tables
    - Desktop (min-width: 992px): Container max-width settings
  - **Standardized Button Hover Effects**: All buttons have consistent 0.2s transitions for background-color, border-color, and color
  - **UI Standardization**: Consistent filter/sort boxes, form inputs, buttons, and labels across all pages for a cohesive user experience

## Testing

The application includes a comprehensive test suite with **139 tests** (100% pass rate) covering unit tests, integration tests, end-to-end tests, and security tests.

**Quick Start:**
```bash
python tests/run_tests.py
```

For detailed testing information, see [SETUP_STEPS.md](SETUP_STEPS.md#-testing).

## Code Quality & Refactoring

The codebase has been refactored to improve maintainability and reduce duplication:

- **Controller Helpers** (`src/utils/controller_helpers.py`): Centralized functions for permission checking, image upload handling, and service result processing
- **Query Builder** (`src/utils/query_builder.py`): Fluent API for building dynamic SQL queries programmatically
- **Reduced Code Duplication**: Image upload logic consolidated from ~50 duplicated lines to reusable functions
- **Standardized Patterns**: Consistent permission checks and error handling across controllers

For detailed information about the codebase structure, see the Project Structure section above.

## Environment Variables

Create a `.env` file in the project root by copying `.env.example`:

```bash
cp .env.example .env
```

**Required:** Set `SECRET_KEY` (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)

For complete environment variable documentation, see `.env.example` and [SETUP_STEPS.md](SETUP_STEPS.md#1-initial-setup).

