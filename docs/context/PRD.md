# Product Requirements Document (PRD)
## Indiana University Campus Resource Hub

**Version:** 2.0 (Concise)  
**Date:** Fall 2025  
**Team:** MSIS Core Team 16

> **Note:** This is a concise overview. For complete technical specifications, see [PRD_COMPLETE.md](PRD_COMPLETE.md). For quick start, see [README.md](../../README.md).

---

## Product Overview

The Indiana University Campus Resource Hub is a full-stack web application that enables university departments, student organizations, and individuals to efficiently list, share, and reserve campus resources including study rooms, AV equipment, lab instruments, event spaces, and tutoring time.

### Objectives
- Enable efficient resource discovery through search and filtering
- Facilitate booking with automated conflict detection
- Support role-based workflows for approvals and management
- Provide transparency through ratings and reviews
- Ensure security through server-side validation and input sanitization
- Demonstrate AI-first development practices with context-aware features

---

## Users & Roles

**Students:**
- Search, filter, book, review, and message resource owners
- Limited to viewing and managing their own bookings

**Staff/Faculty:**
- Create and manage resources they own
- Can approve bookings for any resource

**Administrators:**
- Full system access and oversight
- User management (suspend, role changes, soft delete)
- Resource moderation and management
- System statistics and analytics
- Audit logging for all administrative actions

---

## Core Features

### User Management & Authentication
- User registration with email/password
- Role-based access control (Student, Staff, Admin)
- Profile management with image upload and cropping
- User suspension and soft delete (admin-only)

### Resource Management
- Full CRUD operations for resources
- Multiple image uploads per resource
- Resource-specific operating hours (with 24-hour operation option)
- Resource lifecycle: draft → published → archived
- Categories: study_room, lab_equipment, av_equipment, event_space, tutoring, other

### Search & Discovery
- Keyword search across titles and descriptions
- Filter by category, location, capacity, availability date/time
- Sort by relevance, date, title, capacity, rating, booking count, average rating, recently booked
- Past date/time validation prevents filtering for past availability
- Clear all filters functionality

### Booking & Scheduling
- Interactive calendar view (12 AM - 11:59 PM)
- Drag-and-select time slot selection
- Automatic approval for available slots
- Conflict detection prevents overlapping bookings
- Booking status: approved, pending, denied, in_progress (computed), cancelled, completed
- Booking duration: min 29 minutes, max 8 hours
- Advance booking requirement: minimum 1 hour in future
- Calendar export (Google Calendar, Outlook, iCal)

### Messaging System
- Thread-based messaging between users
- Resource-specific threading
- Read/unread status tracking
- Navbar notifications for unread messages
- Adaptive message bubble sizing

### Reviews & Ratings
- 5-star rating system (1-5)
- Text review comments (optional, max 2000 characters)
- Multiple reviews per user per resource (one review per completed booking)
- Reviews can be linked to completed bookings
- Aggregate rating calculation and display

### AI Concierge "Crimson"
- Natural language resource queries using Google Gemini API
- Markdown rendering in responses (bold, italic)
- Persistent chat history across page navigations
- Context-aware responses based on database content and project documentation (`/docs/context/` files)
- Loads context from PRD.md, ERD_AND_SCHEMA.md, and PRD_COMPLETE.md for improved responses

### Admin Dashboard
- Comprehensive statistics and analytics
- User management with filter modals
- Resource management with filter modals
- Booking management with filter modals
- Admin action logging with filter modals
- Resource statistics page with filtering and sorting

---

## Technology Stack

**Backend:**
- Flask 3.0.0+ (Python web framework)
- SQLite (development), PostgreSQL (production-ready)
- bcrypt (password hashing)
- python-dateutil (timezone handling)

**Frontend:**
- Bootstrap 5 (UI framework)
- Jinja2 (templating)
- JavaScript (ES6+)
- Cropper.js (image cropping)

**AI Integration:**
- Google Gemini API (natural language processing)

**Configuration:**
- Environment variable-based configuration
- Structured logging with file rotation

**Styling:**
- Custom CSS with Indiana University branding (Crimson #990000, White)
- Standardized shadow utility classes
- Responsive design (mobile-first approach)
- UI standardization across all pages

---

## Key Requirements

### Security
- Password hashing using bcrypt (salt rounds: 12)
- SQL injection prevention (parameterized queries)
- XSS prevention (input sanitization)
- CSRF protection (Flask-WTF) - Fully implemented with CSRF tokens on all forms
- Role-based access control
- Server-side validation for all inputs

### Database Schema
- 7 tables: users, resources, bookings, messages, thread_read, reviews, admin_logs
- Soft delete for users (preserves referential integrity)
- No UNIQUE constraint on reviews (allows multiple reviews per completed booking)
- Resource-specific operating hours with 24-hour operation flag
- Restricted resources flag (requires approval for bookings)
- Booking statuses: approved, pending, denied, cancelled, completed

### Validation Rules
- Email must be unique (can be NULL for soft-deleted users)
- Password complexity requirements
- Booking duration: 29 minutes minimum, 8 hours maximum
- Booking advance: minimum 1 hour in future
- Review rating: 1-5 integer
- Review comment: max 2000 characters

### Testing
- Comprehensive test suite: 139 tests (100% pass rate)
- Unit tests, integration tests, end-to-end tests, security tests
- AI feature validation tests

---

## Success Metrics

- Test coverage: 139 tests passing
- User registration and authentication working
- Resource booking with conflict detection working
- AI Concierge providing accurate responses
- All core features functional and tested

---

For detailed technical specifications, database schema, API endpoints, business rules, and complete requirements, see [PRD_COMPLETE.md](PRD_COMPLETE.md).

