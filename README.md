# Indiana University Campus Resource Hub

A full-stack web application for managing and booking campus resources including study rooms, AV equipment, lab instruments, event spaces, and tutoring services.

## Required Deliverable Location
- `docs/` - Documentation
  - `wireframes/` - Wireframe images for key pages
  - `context/` - Project context files (PRD, ERD, schema, etc.)
- `.prompt/` - AI development notes and prompts
- `tests/` - Test suite (139 tests, 100% passing)

GitHub Repository URL: https://github.com/andrpick/AiDD-Final-Project---IU-Campus-Resource-Hub/tree/main

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

  **Important**: The chatbot will only work properly after getting inputting the following API key:

  **AIzaSyBHF2baJuu6dT1x3aRQenLb3oXeSbYS_6A** - This is a free API key from Google and must be added to the .env file you create using the .env.example file.

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
- **Email:** staff@iu.edu
- **Password:** StaffUser1!

### Student User
- **Email:** student@iu.edu
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
- `src/data_access/` - Database access layer
- `src/utils/` - Utility modules
- `src/views/` - Jinja2 templates
- `src/static/` - Static files (CSS, JS, images)
- `tests/` - Test suite (139 tests, 100% passing)
- `uploads/` - User-uploaded files
- `docs/` - Documentation
  - `wireframes/` - Wireframe images for key pages
  - `context/` - Project context files (PRD, ERD, etc.)
- `.prompt/` - AI development notes and prompts

For detailed project structure and architecture information, see [docs/context/PRD_COMPLETE.md](docs/context/PRD_COMPLETE.md#6-architecture--folder-structure).

## Features

The application includes the following core features:

- **User Authentication & Authorization**: Role-based access control (Student, Staff, Admin) with secure password hashing and CSRF protection
- **Resource Management**: Full CRUD operations with multiple image uploads, resource-specific operating hours, and admin archiving
- **Advanced Search & Filtering**: Keyword search, category/location/capacity filtering, availability date/time filtering
- **Booking System**: Calendar-based booking with conflict detection, automatic approval, status tracking, and calendar export
- **Messaging System**: Thread-based messaging with read/unread tracking and notifications
- **Reviews & Ratings**: Multiple reviews per user per resource with star ratings
- **AI Concierge "Crimson"**: Chatbot widget with Google Gemini AI integration for natural language resource queries
- **Admin Dashboard**: Comprehensive statistics, user/resource/booking management, and action logging
- **Email Notifications**: Simulated email notifications for booking confirmations and status changes (logged)

For detailed feature descriptions, see [SETUP_STEPS.md](SETUP_STEPS.md#4-key-features-overview). For complete technical specifications and API documentation, see [docs/context/PRD_COMPLETE.md](docs/context/PRD_COMPLETE.md) and [API.md](API.md).

## Technology Stack

- **Backend**: Flask 3.0.0+, SQLite (development), PostgreSQL (production-ready)
- **Frontend**: Bootstrap 5, Jinja2 templating, JavaScript (ES6+)
- **AI Integration**: Google Gemini API for natural language resource queries
- **Security**: Flask-WTF (CSRF protection), bcrypt (password hashing)
- **Utilities**: Python-dateutil, python-dotenv, custom utility modules
- **Configuration**: Environment variable-based configuration system
- **Logging**: Structured logging with file rotation
- **Styling**: Custom CSS with Indiana University branding (Crimson #990000, White)

For complete technology stack details, see [docs/context/PRD_COMPLETE.md](docs/context/PRD_COMPLETE.md#13-technology-stack).

## AI Integration & Collaboration

This project was developed using an AI-first approach, integrating AI tools throughout the design, development, and testing phases. The team estimates >99% of code was generated by AI through over a hundred iterative prompts. When issues arose, they would be sovled by prompting AI to fix them. **Stitch** was utilized during the design phase to accelerate wireframing, rapidly translating textual requirements into visual layouts while maintaining strategic control over the Indiana University branding and visual identity. **Cursor** served as the primary IDE during implementation, with its embedded AI capabilities significantly accelerating coding and debugging cycles. **Eraser/DiagramGPT** was used to generate the ERD from the mermaid notation markdown file. However, in the GitHub respositor, the mermaid notation is recognized and the diagram can be seen in the 'ERD_AND_SCHEMA' file as well.

The AI Concierge feature "Crimson" demonstrates context-aware AI integration, using Google Gemini API to answer natural language questions about campus resources. The concierge loads context from project documentation files (`/docs/context/`) including PRD, ERD, and technical specifications, ensuring responses are grounded in actual project data rather than fabricated information. This implementation includes automated tests verifying that AI outputs align with factual database content.

Ethical considerations were prioritized throughout development. All AI interactions were meticulously logged in `.prompt/dev_notes.md` with clear attribution, maintaining academic integrity and professional accountability. We established that while AI accelerates development, human oversight remains essential—all AI-generated code underwent rigorous review for security vulnerabilities, architectural adherence, and integration quality. The team maintained full accountability for the final product, balancing AI assistance with manual coding to preserve fundamental programming skills.

Key lessons learned include the importance of iterative prompt refinement, the necessity of comprehensive verification processes, and the value of maintaining transparency in AI-assisted development. This approach enabled delivery of a more comprehensive and polished product than would have been feasible using traditional methods alone, while ensuring quality, security, and maintainability standards were met.

For detailed AI interaction logs and reflection, see [.prompt/dev_notes.md](.prompt/dev_notes.md) and [.prompt/golden_prompts.md](.prompt/golden_prompts.md).

## Testing

The application includes a comprehensive test suite with **139 tests** (100% pass rate) covering unit tests, integration tests, end-to-end tests, and security tests.

**Quick Start:**
```bash
python tests/run_tests.py
```

For detailed testing information, see [SETUP_STEPS.md](SETUP_STEPS.md#-testing). For testing requirements and specifications, see [docs/context/PRD_COMPLETE.md](docs/context/PRD_COMPLETE.md#12-testing-requirements).

## Documentation

- **[SETUP_STEPS.md](SETUP_STEPS.md)** - Detailed setup instructions and feature overview
- **[API.md](API.md)** - API endpoint documentation
- **[docs/context/PRD.md](docs/context/PRD.md)** - High-level Product Requirements Document (1-2 pages)
- **[docs/context/PRD_COMPLETE.md](docs/context/PRD_COMPLETE.md)** - Complete technical specification (comprehensive)
- **[docs/context/ERD_AND_SCHEMA.md](docs/context/ERD_AND_SCHEMA.md)** - Database schema and ERD reference
- **[docs/wireframes/](docs/wireframes/)** - UI wireframes for key pages
- **[.prompt/dev_notes.md](.prompt/dev_notes.md)** - AI development interaction log

## Environment Variables

Create a `.env` file in the project root by copying `.env.example`:

```bash
cp .env.example .env
```

**Required:** Set `SECRET_KEY` (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)

For complete environment variable documentation, see `.env.example` and [SETUP_STEPS.md](SETUP_STEPS.md#1-initial-setup).

---

## Additional Resources

- **API Documentation**: See [API.md](API.md) for endpoint specifications and request/response examples
- **Database Schema**: See [docs/context/ERD_AND_SCHEMA.md](docs/context/ERD_AND_SCHEMA.md) for database structure reference
- **Complete Technical Specs**: See [docs/context/PRD_COMPLETE.md](docs/context/PRD_COMPLETE.md) for comprehensive requirements and implementation details
- **AI Development Log**: See [.prompt/dev_notes.md](.prompt/dev_notes.md) for AI tool usage and reflection

