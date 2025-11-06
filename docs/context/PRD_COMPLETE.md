# Product Requirements Document (PRD) - Complete Technical Specification
## Indiana University Campus Resource Hub

**Version:** 2.0 (Complete Technical Specification)  
**Date:** Fall 2025  
**Team:** AiDD Capstone Project Team  
**Purpose:** This document contains all product and technical requirements needed to recreate the Indiana University Campus Resource Hub application from scratch.

---

## Table of Contents

1. [Product Overview](#1-product-overview)
2. [Stakeholders & Users](#2-stakeholders--users)
3. [Core Features](#3-core-features)
4. [Database Schema](#4-database-schema)
5. [API Endpoints](#5-api-endpoints)
6. [Architecture & Folder Structure](#6-architecture--folder-structure)
7. [Business Rules & Algorithms](#7-business-rules--algorithms)
8. [Validation Rules](#8-validation-rules)
9. [Security Requirements](#9-security-requirements)
10. [User Interface Specifications](#10-user-interface-specifications)
11. [AI Feature Specifications](#11-ai-feature-specifications)
12. [Testing Requirements](#12-testing-requirements)
13. [Technology Stack](#13-technology-stack)
14. [Deployment & Operations](#14-deployment--operations)
15. [Optional Advanced Features](#15-optional-advanced-features-top-projects)
16. [Non-Goals](#16-non-goals-out-of-scope-for-mvp)
17. [Success Metrics](#17-success-metrics)

---

## 1. Product Overview

### 1.1 Objective

The Indiana University Campus Resource Hub is a full-stack web application that enables university departments, student organizations, and individuals to efficiently list, share, and reserve campus resources including study rooms, AV equipment, lab instruments, event spaces, and tutoring time. The system aims to reduce resource allocation friction, improve utilization rates, and provide a seamless booking experience for the campus community.

### 1.2 Project Goals

- Enable efficient resource discovery through search and filtering
- Facilitate booking with automated conflict detection
- Support role-based workflows for approvals and management
- Provide transparency through ratings and reviews
- Ensure security through server-side validation and input sanitization
- Demonstrate AI-first development practices with context-aware features

---

## 2. Stakeholders & Users

### 2.1 Primary Users

**Students:**
- Need to find and book study spaces, equipment, and tutoring services
- Can search, filter, book, review, and message resource owners
- Limited to viewing and managing their own bookings

**Staff/Faculty:**
- Manage and share department resources
- Approve or reject booking requests
- Can create and manage resources they own
- Can approve bookings for any resource

**Administrators:**
- Full system access and oversight
- User management (suspend, role changes, delete)
- Resource moderation and management
- System statistics and analytics
- Audit logging for all administrative actions

### 2.2 Secondary Stakeholders

- **University IT Department:**** System maintenance and security
- **Campus Facilities Management:** Resource inventory tracking
- **Student Organizations:** Event space booking and coordination

---

## 3. Core Features

### 3.1 User Management & Authentication

**Requirements:**
- User registration with email/password
- User login/logout with session management
- Password hashing using bcrypt (salt rounds: 12)
- Role-based access control (Student, Staff, Admin)
- Profile management (name, email, department, profile image)
- User suspension system for administrators

**Functionality:**
- Email must be unique
- Password must meet complexity requirements (see Validation Rules)
- Role determines access to approval and management workflows
- Suspended users cannot login or create content
- Profile updates require authentication

### 3.2 Resource Management

**Requirements:**
- Full CRUD operations for resources
- Resource fields: title, description, images, category, location, capacity, availability_rules, status, owner_id
- Resource lifecycle: draft → published → archived
- Owner-based resource management
- Category filtering and organization

**Functionality:**
- Only authenticated users can create resources
- Resource owner or admin can edit/delete resources
- Resources start as 'draft' status
- Only 'published' resources are visible in public listings
- Owners can see their own draft resources
- Resources can be archived (soft delete equivalent)

**Resource Categories:**
- `study_room` - Study spaces and rooms
- `lab_equipment` - Laboratory equipment and instruments
- `av_equipment` - Audio/visual equipment
- `event_space` - Event and meeting spaces
- `tutoring` - Tutoring services and time slots
- `other` - Other resource types

### 3.3 Search & Discovery

**Requirements:**
- Keyword search across resource titles and descriptions (case-insensitive, partial match)
- Filter by category, location, capacity (min/max), availability date/time
- Sort options: relevance (when search keyword provided), created_at (newest/oldest), title (alphabetical), capacity, rating
- Pagination support (default 20 per page, max 100)
- Availability checking against existing bookings

**Functionality:**
- Search uses LIKE queries with parameterized statements
- Filters can be combined (AND logic)
- Sort applies after filtering
- Availability filter checks against approved and pending bookings
- Results include resource metadata and availability status

### 3.4 Booking & Scheduling

**Requirements:**
- Calendar-based booking with start/end datetime selection
- Interactive month-view calendar for date selection
- Day-view with drag-and-select time slot selection (12 AM - 11:59 PM)
- Current time indicator on the current day
- Conflict detection algorithm (see Business Rules)
- Approval workflow: automatic approval for available slots (no manual approval needed)
- Booking status management: approved → cancelled/completed (simplified workflow)
- Booking duration constraints (min 29 minutes, max 8 hours)
- Resource-specific operating hours constraints (set by owner/admin, 12-hour format input)
- Resources can operate 24 hours a day (is_24_hours flag)
- Advance booking requirement (must be at least 1 hour in future)
- Calendar export to Google Calendar, Outlook, and iCal formats
- Email notifications or simulated notifications for booking confirmations and changes

**Functionality:**
- Only authenticated users can request bookings
- Bookings are automatically approved when created (no pending/rejected statuses)
- Conflict detection prevents overlapping bookings
- Booking requester or admin can cancel bookings
- Completed bookings (past end time) are eligible for reviews
- Calendar displays all time slots from 12 AM to 11:59 PM
- Slots outside operating hours are displayed but marked as unavailable (grayed out)
- For 24-hour resources, all slots are available for booking
- Email notifications or simulated notifications sent for booking confirmations and status changes

**Booking Status Flow:**
```
approved → cancelled (by requester/admin)
approved → completed (after booking end time passes)
```

**Status Values:**
- `approved` - Booking has been created and approved automatically (default status)
- `cancelled` - Booking has been cancelled by requester or admin
- `completed` - Booking has passed its end time (used for review eligibility)

### 3.5 Messaging System

**Requirements:**
- Thread-based messaging between users
- In-app messaging interface
- Message threading (consistent thread_id for conversations between two users)
- Unread message tracking
- Soft delete (mark deleted, don't remove from DB)

**Functionality:**
- Users can send messages to other users
- Messages grouped by thread_id (deterministic: smaller_user_id + larger_user_id)
- Thread list sorted by most recent message
- Unread count per thread
- Users can only view threads they're part of
- Message content sanitized for XSS

### 3.6 Reviews & Ratings

**Requirements:**
- 5-star rating system (1-5 integer)
- Text review comments (optional, max 2000 characters)
- One review per user per resource (enforced at database level)
- Reviews can be linked to completed bookings (optional booking_id)
- Aggregate rating calculation and display
- Rating distribution statistics

**Functionality:**
- Users can submit reviews after booking completion (booking must have status 'completed' or past end time)
- One review per user per resource constraint
- Reviews can be updated within 30 days
- Users can delete their own reviews
- Admins can delete any review
- Aggregate stats: average_rating, total_reviews, rating_distribution (count per star level)
- Reviews can optionally link to a completed booking_id

### 3.7 Admin Dashboard

**Requirements:**
- User management (list, suspend, role changes, delete)
- Resource oversight and moderation
- System statistics and analytics
- Admin action logging for audit trail
- Booking management

**Statistics Displayed:**
- Total users by role
- Total resources by category and status
- Total bookings by status
- Total reviews
- Active users in last 30 days
- Popular resources (most booked)
- Busiest times (booking frequency patterns)

**Admin Functions:**
- Search users by name, email, role, department
- Suspend users with reason
- Change user roles (with constraints)
- Delete users (with cascade: archive resources, cancel bookings)
- View admin action logs with filtering

**Role Change Constraints:**
- student → staff (allowed)
- student → admin (requires admin approval log)
- staff → admin (allowed)
- admin → student/staff (requires another admin to perform)
- Admin cannot remove their own admin role (self-demotion prevention)

### 3.8 AI-Powered Resource Concierge

**Requirements:**
- Natural language query interface
- Context-aware recommendations based on project data
- Integration with database for factual responses
- References context files from `/docs/context/` for grounding
- Never returns fabricated or unverifiable results

**Functionality:**
- Users can ask questions in natural language
- System parses query to extract search parameters
- Searches resources and provides factual recommendations
- Uses context files (PRD, personas, etc.) to inform responses
- Validates all responses against actual database content
- Provides summary statistics upon request

**AI Feature Requirements:**
- Must include at least one example where AI-generated code references materials from `/docs/context/`
- All AI outputs must be validated against factual project data
- AI components must never return fabricated information
- Must provide automated or manual test verifying AI outputs behave predictably

---

## 4. Database Schema

### 4.1 Tables

#### users
```sql
CREATE TABLE users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('student', 'staff', 'admin')),
    department TEXT,
    profile_image TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    suspended BOOLEAN DEFAULT 0,
    suspended_reason TEXT,
    suspended_at DATETIME,
    deleted BOOLEAN DEFAULT 0,
    deleted_at DATETIME,
    deleted_by INTEGER
);
```

**Constraints:**
- `email` must be unique
- `role` must be one of: 'student', 'staff', 'admin'
- `password_hash` never returned in API responses
- `suspended` defaults to 0 (false)

#### resources
```sql
CREATE TABLE resources (
    resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
    owner_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL CHECK(category IN ('study_room', 'lab_equipment', 'av_equipment', 'event_space', 'tutoring', 'other')),
    location TEXT NOT NULL,
    capacity INTEGER CHECK(capacity IS NULL OR capacity > 0),
    images TEXT,  -- JSON array of image paths
    availability_rules TEXT,  -- JSON blob describing recurring availability
    operating_hours_start INTEGER NOT NULL DEFAULT 8 CHECK(operating_hours_start >= 0 AND operating_hours_start <= 23),
    operating_hours_end INTEGER NOT NULL DEFAULT 22 CHECK(operating_hours_end >= 0 AND operating_hours_end <= 23),
    is_24_hours BOOLEAN DEFAULT 0,
    status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'published', 'archived')),
    featured BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (owner_id) REFERENCES users(user_id)
);
```

**Constraints:**
- `owner_id` must reference existing user
- `category` must be from allowed enum
- `capacity` can be NULL or greater than 0
- `operating_hours_start` must be between 0 and 23 (inclusive)
- `operating_hours_end` must be between 0 and 23 (inclusive)
- `status` defaults to 'draft'
- `images` stored as JSON array string
- `availability_rules` stored as JSON object string

#### bookings
```sql
CREATE TABLE bookings (
    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id INTEGER NOT NULL,
    requester_id INTEGER NOT NULL,
    start_datetime DATETIME NOT NULL,
    end_datetime DATETIME NOT NULL,
    status TEXT DEFAULT 'approved' CHECK(status IN ('approved', 'cancelled', 'completed')),
    rejection_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id),
    FOREIGN KEY (requester_id) REFERENCES users(user_id)
);
```

**Constraints:**
- `resource_id` and `requester_id` must reference existing records
- `status` defaults to 'approved' (bookings are auto-approved when created)
- `rejection_reason` optional (rejected status no longer used in simplified workflow)
- `end_datetime` must be after `start_datetime`
- Conflict detection enforced at application level

#### messages
```sql
CREATE TABLE messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    thread_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    receiver_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    read BOOLEAN DEFAULT 0,
    deleted BOOLEAN DEFAULT 0,
    FOREIGN KEY (sender_id) REFERENCES users(user_id),
    FOREIGN KEY (receiver_id) REFERENCES users(user_id)
);
```

**Constraints:**
- `sender_id` and `receiver_id` must reference existing users
- `sender_id` cannot equal `receiver_id`
- `thread_id` generated deterministically from user IDs
- `read` and `deleted` default to 0 (false)
- Soft delete used (deleted flag, not hard delete)

#### reviews
```sql
CREATE TABLE reviews (
    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id INTEGER NOT NULL,
    reviewer_id INTEGER NOT NULL,
    booking_id INTEGER,
    rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
    comment TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id),
    FOREIGN KEY (reviewer_id) REFERENCES users(user_id),
    FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
    UNIQUE(resource_id, reviewer_id)
);
```

**Constraints:**
- `resource_id` and `reviewer_id` must reference existing records
- `booking_id` optional but must reference existing booking if provided
- `rating` must be integer between 1 and 5
- `comment` max 2000 characters
- `UNIQUE(resource_id, reviewer_id)` enforces one review per user per resource

#### admin_logs
```sql
CREATE TABLE admin_logs (
    log_id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    target_table TEXT,
    target_id INTEGER,
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (admin_id) REFERENCES users(user_id)
);
```

**Constraints:**
- `admin_id` must reference existing user
- `action` required (e.g., 'suspend_user', 'change_role', 'delete_user')
- Logs are immutable (cannot be deleted or modified)
- Used for audit trail

### 4.2 Indexes

**Performance indexes:**
```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_resources_owner ON resources(owner_id);
CREATE INDEX idx_resources_status ON resources(status);
CREATE INDEX idx_resources_category ON resources(category);
CREATE INDEX idx_bookings_resource ON bookings(resource_id);
CREATE INDEX idx_bookings_requester ON bookings(requester_id);
CREATE INDEX idx_bookings_datetime ON bookings(start_datetime, end_datetime);
CREATE INDEX idx_messages_thread ON messages(thread_id);
CREATE INDEX idx_reviews_resource ON reviews(resource_id);
CREATE INDEX idx_reviews_reviewer ON reviews(reviewer_id);
```

### 4.3 Relationships

- **users** → **resources** (1:N via owner_id)
- **users** → **bookings** (1:N via requester_id)
- **users** → **reviews** (1:N via reviewer_id)
- **users** → **messages** (1:N via sender_id and receiver_id)
- **users** → **admin_logs** (1:N via admin_id)
- **resources** → **bookings** (1:N via resource_id)
- **resources** → **reviews** (1:N via resource_id)
- **bookings** → **reviews** (1:N via booking_id, optional)

---

## 5. API Endpoints

### 5.1 Authentication Endpoints

**Base URL:** `/auth`

| Method | Route | Description | Auth Required |
|--------|-------|-------------|---------------|
| GET, POST | `/register` | User registration | No |
| GET, POST | `/login` | User login | No |
| GET | `/logout` | User logout | Yes |
| GET | `/profile/<int:user_id>` | View user profile | Yes |
| GET, POST | `/profile/<int:user_id>/edit` | Edit user profile | Yes (own profile or admin) |

**Request/Response Examples:**

```
POST /auth/register
Content-Type: application/x-www-form-urlencoded

name=John Doe&email=john@example.com&password=SecurePass123!&role=student

Response: Redirect to login page or error message
```

```
POST /auth/login
Content-Type: application/x-www-form-urlencoded

email=john@example.com&password=SecurePass123!

Response: Redirect to homepage or error message
```

### 5.2 Resource Endpoints

**Base URL:** `/resources`

| Method | Route | Description | Auth Required |
|--------|-------|-------------|---------------|
| GET | `/` | List all published resources | No |
| GET | `/<int:resource_id>` | View resource details | No |
| GET, POST | `/create` | Create new resource | Yes |
| GET, POST | `/<int:resource_id>/edit` | Edit resource | Yes (owner or admin) |
| POST | `/<int:resource_id>/delete` | Delete resource | Yes (owner or admin) |
| GET | `/my-resources` | List user's own resources | Yes |

### 5.3 Booking Endpoints

**Base URL:** `/bookings`

| Method | Route | Description | Auth Required |
|--------|-------|-------------|---------------|
| GET | `/` | List user's bookings | Yes |
| POST | `/create` | Create booking request | Yes |
| GET | `/<int:booking_id>` | View booking details | Yes |
| POST | `/<int:booking_id>/approve` | Approve booking | Yes (owner/staff/admin) |
| POST | `/<int:booking_id>/reject` | Reject booking | Yes (owner/staff/admin) |
| POST | `/<int:booking_id>/cancel` | Cancel booking | Yes (requester or admin) |
| POST | `/check-conflicts` | Check for conflicts | Yes |

**Request Example:**
```
POST /bookings/create
Content-Type: application/x-www-form-urlencoded

resource_id=1&start_datetime=2025-12-15T10:00:00&end_datetime=2025-12-15T12:00:00
```

### 5.4 Search Endpoints

**Base URL:** `/search`

| Method | Route | Description | Auth Required |
|--------|-------|-------------|---------------|
| GET | `/` | Search resources with filters | No |
| GET | `/filters` | Get available filter values | No |

**Query Parameters:**
- `keyword` - Search keyword
- `category` - Filter by category
- `location` - Filter by location
- `capacity_min` - Minimum capacity
- `capacity_max` - Maximum capacity
- `available_from` - Available from datetime (ISO format)
- `available_to` - Available to datetime (ISO format)
- `sort_by` - Sort field (relevance, created_at, title, capacity, rating)
- `sort_order` - Sort direction (asc, desc)
- `page` - Page number (default: 1)
- `page_size` - Results per page (default: 20, max: 100)

### 5.5 Messaging Endpoints

**Base URL:** `/messages`

| Method | Route | Description | Auth Required |
|--------|-------|-------------|---------------|
| GET | `/` | List message threads | Yes |
| GET | `/thread/<int:thread_id>` | View thread messages | Yes |
| POST | `/send` | Send message | Yes |
| POST | `/<int:message_id>/delete` | Delete message | Yes |

### 5.6 Review Endpoints

**Base URL:** `/reviews`

| Method | Route | Description | Auth Required |
|--------|-------|-------------|---------------|
| GET | `/resource/<int:resource_id>` | List reviews for resource | No |
| POST | `/create` | Submit review | Yes |
| GET, POST | `/<int:review_id>/edit` | Edit review | Yes (own review) |
| POST | `/<int:review_id>/delete` | Delete review | Yes (own review or admin) |

### 5.7 Admin Endpoints

**Base URL:** `/admin`

| Method | Route | Description | Auth Required |
|--------|-------|-------------|---------------|
| GET | `/` | Admin dashboard | Yes (admin) |
| GET | `/users` | List all users | Yes (admin) |
| POST | `/users/<int:user_id>/role` | Change user role | Yes (admin) |
| POST | `/users/<int:user_id>/suspend` | Suspend user | Yes (admin) |
| POST | `/users/<int:user_id>/unsuspend` | Unsuspend user | Yes (admin) |
| POST | `/users/<int:user_id>/delete` | Delete user | Yes (admin) |
| GET | `/logs` | View admin logs | Yes (admin) |

### 5.8 AI Concierge Endpoints

**Base URL:** `/ai`

| Method | Route | Description | Auth Required |
|--------|-------|-------------|---------------|
| GET, POST | `/concierge` | Natural language query | No |
| GET | `/recommendations` | Get resource recommendations | No |
| GET | `/summary` | Get system summary | No |
| GET | `/scheduler` | Get AI scheduling suggestions | Yes |

### 5.9 Optional Feature Endpoints

#### 5.9.1 Calendar Integration Endpoints

**Base URL:** `/calendar`

| Method | Route | Description | Auth Required |
|--------|-------|-------------|---------------|
| GET | `/google/connect` | Initiate Google Calendar OAuth | Yes |
| GET | `/google/callback` | OAuth callback handler | Yes |
| POST | `/google/disconnect` | Disconnect Google Calendar | Yes |
| GET | `/google/sync` | Manually sync bookings to Google Calendar | Yes |
| GET | `/export.ics` | Export bookings as iCal file | Yes |
| GET | `/export.ics?booking_id=<id>` | Export single booking as iCal | Yes |

#### 5.9.2 Waitlist Endpoints

**Base URL:** `/waitlist`

| Method | Route | Description | Auth Required |
|--------|-------|-------------|---------------|
| POST | `/join` | Join waitlist for resource | Yes |
| GET | `/` | List user's waitlist entries | Yes |
| GET | `/resource/<int:resource_id>` | List waitlist for resource (owner/admin) | Yes (owner/admin) |
| POST | `/<int:waitlist_id>/cancel` | Cancel waitlist entry | Yes |
| POST | `/<int:waitlist_id>/promote` | Promote waitlist entry to booking (owner/admin) | Yes (owner/admin) |

#### 5.9.3 Analytics Endpoints

**Base URL:** `/analytics`

| Method | Route | Description | Auth Required |
|--------|-------|-------------|---------------|
| GET | `/department` | Department-specific reports | Yes (staff/admin) |
| GET | `/resource-type` | Resource type analytics | Yes (admin) |
| GET | `/user-activity` | User activity reports | Yes (admin) |
| GET | `/booking-patterns` | Booking patterns analysis | Yes (admin) |
| GET | `/my-activity` | Personal activity report | Yes |
| GET | `/export/csv` | Export analytics data as CSV | Yes (admin) |
| GET | `/export/json` | Export analytics data as JSON | Yes (admin) |

#### 5.9.4 Advanced Search Endpoints

**Base URL:** `/search`

Additional routes for advanced search:

| Method | Route | Description | Auth Required |
|--------|-------|-------------|---------------|
| GET | `/semantic` | Semantic search with embeddings | No |
| GET | `/hybrid` | Hybrid keyword + semantic search | No |

**Query Parameters:**
- `query` - Natural language search query
- `mode` - 'keyword', 'semantic', or 'hybrid' (default: 'hybrid')
- `limit` - Max results (default: 20, max: 100)

---

## 6. Architecture & Folder Structure

### 6.1 MVC Architecture

The application follows Model-View-Controller (MVC) architecture with clear separation of concerns:

- **Model Layer:** Database models and business logic entities (`src/models/`)
- **View Layer:** Jinja2 templates for UI rendering (`src/views/`)
- **Controller Layer:** Flask routes and blueprints (`src/controllers/`)
- **Service Layer:** Business logic and validation (`src/services/`)
- **Data Access Layer:** Database operations (encapsulated in `src/data_access/`)

**Principle:** Controllers must never issue raw SQL. All database operations go through the data access layer or service layer.

### 6.2 Folder Structure

```
campus-resource-hub/
├── app.py                          # Flask application entry point
├── init_db.py                      # Database initialization script
├── requirements.txt                # Python dependencies
├── README.md                       # Setup and usage instructions
├── .gitignore                      # Git ignore rules
├── .prompt/                        # AI-first development folder
│   ├── dev_notes.md                # AI usage log
│   └── golden_prompts.md            # Most effective prompts
├── docs/                           # Documentation
│   ├── PRD.md                      # Product Requirements Document
│   ├── PRD_COMPLETE.md             # This document
│   ├── ER_DIAGRAM.md               # Database schema documentation
│   ├── WIREFRAMES.md               # UI wireframes
│   ├── DEMO_SCRIPT.md              # Demo presentation script
│   ├── SUBMISSION_CHECKLIST.md     # Submission checklist
│   ├── COMPLETION_REPORT.md        # Project completion report
│   └── context/                    # Context-aware development files
│       ├── APA/                    # Agility, Processes & Automation artifacts
│       ├── DT/                     # Design Thinking artifacts
│       ├── PM/                     # Product Management materials
│       └── shared/                 # Common context files
├── src/                            # Source code
│   ├── controllers/                # Flask blueprints (route handlers)
│   │   ├── __init__.py
│   │   ├── auth_controller.py
│   │   ├── resources_controller.py
│   │   ├── bookings_controller.py
│   │   ├── search_controller.py
│   │   ├── messages_controller.py
│   │   ├── reviews_controller.py
│   │   ├── admin_controller.py
│   │   └── ai_concierge_controller.py
│   ├── models/                     # Data models
│   │   ├── __init__.py
│   │   └── user.py                 # User model (Flask-Login compatible)
│   ├── views/                      # Jinja2 templates
│   │   ├── base.html               # Base template
│   │   ├── home.html               # Homepage
│   │   ├── auth/                   # Authentication templates
│   │   ├── resources/              # Resource templates
│   │   ├── bookings/               # Booking templates
│   │   ├── messages/               # Messaging templates
│   │   ├── reviews/                # Review templates
│   │   ├── admin/                  # Admin templates
│   │   └── ai_concierge/           # AI Concierge templates
│   ├── services/                   # Business logic layer
│   │   ├── __init__.py
│   │   ├── auth_service.py         # Authentication logic
│   │   ├── resource_service.py     # Resource management logic
│   │   ├── booking_service.py      # Booking logic with conflict detection
│   │   ├── calendar_service.py     # Calendar processing utilities
│   │   ├── search_service.py       # Search and filtering logic
│   │   ├── messaging_service.py    # Messaging logic
│   │   ├── review_service.py       # Review and rating logic
│   │   ├── admin_service.py        # Admin utilities
│   │   └── ai_concierge.py        # AI Concierge logic
│   ├── utils/                      # Utility modules
│   │   ├── __init__.py
│   │   ├── config.py              # Centralized configuration management
│   │   ├── exceptions.py          # Custom exception classes
│   │   ├── logging_config.py     # Logging configuration
│   │   ├── datetime_utils.py     # Datetime parsing and formatting utilities
│   │   ├── json_utils.py         # JSON parsing utilities
│   │   ├── html_utils.py         # HTML sanitization utilities
│   │   └── decorators.py         # Common decorators (admin_required, etc.)
│   ├── data_access/                # Database access layer
│   │   ├── __init__.py
│   │   └── database.py             # Database connection utilities
│   └── static/                     # Static files (CSS, JS, images)
│       ├── css/
│       ├── js/
│       └── images/
├── tests/                          # Test suite (52 tests, all passing)
│   ├── run_tests.py                # Test runner script
│   ├── test_app_integration.py
│   ├── test_auth_integration.py
│   ├── test_booking_e2e.py
│   ├── test_booking_service.py
│   ├── test_data_access.py
│   ├── test_security.py
│   └── ai_eval/                    # AI feature validation tests
│       └── test_ai_concierge.py
├── uploads/                        # User-uploaded files
├── logs/                           # Application logs (auto-generated)
├── .env.example                    # Environment variable template
├── .env                            # Environment variables (not in git)
└── campus_resource_hub.db          # SQLite database (included with project)

```

### 6.3 Blueprint Organization

Each feature module has its own blueprint:

- `auth_bp` - Authentication (`/auth`)
- `resources_bp` - Resources (`/resources`)
- `bookings_bp` - Bookings (`/bookings`)
- `search_bp` - Search (`/search`)
- `messages_bp` - Messaging (`/messages`)
- `reviews_bp` - Reviews (`/reviews`)
- `admin_bp` - Admin (`/admin`)
- `ai_concierge_bp` - AI Concierge (`/ai`)

All blueprints registered in `app.py` with proper URL prefixes.

### 6.4 Service Layer Responsibilities

Services handle:
- Business logic validation
- Input sanitization
- Database operations (via data access layer)
- Error handling and return standardized response format: `{'success': bool, 'data/error': ...}`
- Never return raw database objects or passwords

### 6.5 Data Access Layer

Encapsulates all database operations:
- Connection management (context manager pattern)
- Query execution
- Transaction management
- Parameterized queries (SQL injection prevention)
- Returns standardized data structures
- Error handling with custom exceptions (`DatabaseError`)
- Logging for database operations

### 6.6 Utility Layer

Centralized utility modules (`src/utils/`):
- **Configuration**: `config.py` - Environment variable-based configuration with validation
- **Exceptions**: `exceptions.py` - Custom exception classes for error categorization
- **Logging**: `logging_config.py` - Structured logging with file rotation
- **Datetime**: `datetime_utils.py` - Datetime parsing, timezone conversion, formatting
- **JSON**: `json_utils.py` - Safe JSON parsing and serialization
- **HTML**: `html_utils.py` - HTML sanitization and unescaping
- **Decorators**: `decorators.py` - Common decorators (`admin_required`, etc.)

All utilities are exported through `src/utils/__init__.py` for easy importing.

---

## 7. Business Rules & Algorithms

### 7.1 Conflict Detection Algorithm

Two bookings conflict if they overlap in time for the same resource.

**Overlap Check:**
```
Two time ranges overlap if:
(new_start < existing_end) AND (new_end > existing_start)
```

**Implementation Details:**
- Only check against bookings with status 'approved' or 'pending'
- Ignore 'cancelled', 'rejected', and 'completed' bookings (completed bookings are past and no longer active)
- For recurring bookings, check all recurrence instances for conflicts
- Return all conflicting bookings with details
- Use parameterized SQL queries with datetime comparisons

**SQL Query:**
```sql
SELECT * FROM bookings 
WHERE resource_id = ? 
AND status IN ('pending', 'approved')
AND ((start_datetime < ? AND end_datetime > ?) 
     OR (start_datetime < ? AND end_datetime > ?)
     OR (start_datetime >= ? AND end_datetime <= ?))
```

### 7.2 Thread ID Generation

Message threads are identified by a deterministic thread_id based on user IDs.

**Algorithm:**
```python
def generate_thread_id(user1_id, user2_id):
    smaller_id = min(user1_id, user2_id)
    larger_id = max(user1_id, user2_id)
    thread_id = hash(f"{smaller_id}_{larger_id}")  # Or simple concatenation
    return thread_id
```

All messages between the same two users share the same thread_id.

### 7.3 Booking Approval Workflow

**Automatic Approval:**
- Currently all bookings require approval (no auto-approve flag implemented in v1)

**Manual Approval:**
- Resource owner can approve/reject
- Staff role can approve/reject
- Admin role can approve/reject

**Approval Steps:**
1. Check user permissions (owner/staff/admin)
2. Verify booking status is 'pending'
3. Re-check for conflicts (may have been created since request)
4. Update booking status to 'approved'
5. Log admin action if applicable

**Rejection Steps:**
1. Check user permissions
2. Verify booking status is 'pending'
3. Require rejection_reason (max 500 characters)
4. Update booking status to 'rejected'
5. Log admin action if applicable

### 7.4 Aggregate Rating Calculation

**Formula:**
```
average_rating = SUM(ratings) / COUNT(reviews)
rating_distribution = COUNT per star level (1, 2, 3, 4, 5)
```

**SQL Implementation:**
```sql
SELECT 
    AVG(rating) as average_rating,
    COUNT(*) as total_reviews,
    SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END) as rating_5,
    SUM(CASE WHEN rating = 4 THEN 1 ELSE 0 END) as rating_4,
    -- ... for each star level
FROM reviews
WHERE resource_id = ?
```

### 7.5 User Suspension Logic

**Suspend User:**
1. Set `suspended = 1`
2. Set `suspended_reason` (required, max 500 characters)
3. Set `suspended_at = CURRENT_TIMESTAMP`
4. User cannot login
5. User cannot create new content
6. Existing content remains visible but marked

**Unsuspend User:**
1. Set `suspended = 0`
2. Clear `suspended_reason = NULL`
3. Clear `suspended_at = NULL`
4. User regains normal access

### 7.6 User Deletion Cascade Rules (Soft Delete Implementation)

When admin deletes a user, the system performs a **soft delete** (not a hard delete) to preserve data integrity:

1. **User Record**: 
   - Sets `deleted = 1`, `deleted_at = CURRENT_TIMESTAMP`, `deleted_by = admin_id`
   - Anonymizes PII: sets email to NULL, name to '[Deleted User]', clears password_hash, department, profile_image
   - Clears suspension status (suspended = 0, suspended_reason = NULL, suspended_at = NULL)
   - User record remains in database for referential integrity

2. **User's Resources**: 
   - Mark user's resources as 'archived' (status → 'archived')
   - Resources remain accessible but archived
   - Admin can reassign ownership to another user if needed

3. **User's Bookings**: 
   - Cancel user's active bookings (status → 'cancelled')
   - Historical bookings remain in database

4. **Reviews**: 
   - Keep all reviews created by deleted user
   - Display reviewer as "[Deleted User]" in review listings
   - Use LEFT JOIN to handle deleted users gracefully

5. **Messages**: 
   - Keep all messages but anonymize sender/receiver names
   - Display "[Deleted User]" for deleted users in thread listings
   - Messages remain accessible for context

6. **Authentication**: 
   - Deleted users cannot log in (authenticate_user checks deleted status)
   - Email address becomes available for new registrations (deleted users excluded from uniqueness check)

7. **Search & Queries**: 
   - Deleted users excluded from user searches and listings (default behavior)
   - Admin can optionally include deleted users with `include_deleted` parameter
   - Statistics exclude deleted users from active user counts

8. **Admin Actions**: 
   - Cannot suspend, unsuspend, change role, or update deleted users
   - Cannot delete already deleted users
   - Log admin action in admin_logs table

**Benefits of Soft Delete:**
- Preserves referential integrity (no orphaned records)
- Enables data recovery if needed
- Maintains audit trail and compliance
- Graceful handling of deleted users throughout the application

---

## 8. Validation Rules

### 8.1 User Registration & Profile

**Name:**
- Required: Yes
- Length: 2-100 characters
- Allowed characters: Letters, spaces, hyphens, apostrophes
- No special characters except spaces, hyphens, apostrophes

**Email:**
- Required: Yes
- Format: Valid email format (regex validation)
- Length: Max 255 characters
- Uniqueness: Must be unique in database
- Case-insensitive for uniqueness check

**Password:**
- Required: Yes
- Minimum length: 8 characters
- Complexity requirements:
  - At least one uppercase letter
  - At least one lowercase letter
  - At least one number
  - At least one special character
- Hashing: bcrypt with 12 salt rounds
- Never stored in plaintext
- Never returned in API responses

**Role:**
- Required: Yes
- Allowed values: 'student', 'staff', 'admin'
- Case-sensitive
- Default: 'student' for registration

**Department:**
- Required: No
- Length: Max 100 characters
- Optional field

**Profile Image:**
- Required: No
- Type: File path or URL
- Validation: File type restrictions, size limits (max 16MB)
- Path traversal prevention

### 8.2 Resource Management

**Title:**
- Required: Yes
- Length: 5-200 characters
- Sanitization: HTML/script tags removed

**Description:**
- Required: No
- Length: Max 5000 characters
- Sanitization: HTML/script tags removed

**Category:**
- Required: Yes
- Allowed values: 'study_room', 'lab_equipment', 'av_equipment', 'event_space', 'tutoring', 'other'
- Case-sensitive
- Must match enum exactly

**Location:**
- Required: Yes
- Length: Max 200 characters

**Capacity:**
- Required: No (optional)
- Type: Integer
- Range: Must be NULL or greater than 0
- Allows NULL values for resources without capacity limits

**Images:**
- Required: No
- Format: JSON array of strings (file paths)
- Max items: 10 images
- Path validation: Prevent path traversal
- File type restrictions

**Availability Rules:**
- Required: No
- Format: JSON object string
- Structure: Valid JSON, custom schema
- Validation: JSON parsing and structure check

**Operating Hours:**
- Required: Yes (must be set by resource owner/admin)
- Format: 12-hour format (hour 1-12 + AM/PM) during input, stored as 24-hour format (0-23) in database
- Start Hour: Integer between 0-23 (default: 8 for 8 AM)
- End Hour: Integer between 0-23 (default: 22 for 10 PM)
- 24-Hour Operation: Boolean flag (`is_24_hours`) to mark resource as operating 24 hours a day
- When `is_24_hours` is True, operating hours constraints are bypassed and all slots are available
- Validation: Start hour must be less than end hour (unless 24-hour operation)

**Status:**
- Required: No (defaults to 'draft')
- Allowed values: 'draft', 'published', 'archived'
- Default: 'draft'

### 8.3 Booking Validation

**Resource ID:**
- Required: Yes
- Type: Integer
- Validation: Must exist in resources table
- Resource must be 'published' status

**Start Datetime:**
- Required: Yes
- Format: ISO 8601 datetime string
- Validation: Must be valid datetime
- Must be in the future (at least 1 hour from now)
- Must be during resource's operating hours (unless resource operates 24 hours)

**End Datetime:**
- Required: Yes
- Format: ISO 8601 datetime string
- Validation: Must be valid datetime
- Must be after start_datetime
- Must be during resource's operating hours (unless resource operates 24 hours)

**Duration:**
- Minimum: 29 minutes
- Maximum: 8 hours
- Calculated: end_datetime - start_datetime

**Operating Hours:**
- Each resource has configurable operating hours set by owner/admin
- Operating hours are specified in 12-hour format (hour + AM/PM) during resource creation/editing
- Stored in database as 24-hour format (0-23) for `operating_hours_start` and `operating_hours_end`
- Resources can be marked as 24-hour operation (`is_24_hours` flag), which overrides operating hours constraints
- Calendar displays all time slots from 12 AM to 11:59 PM
- Slots outside operating hours are displayed but marked as unavailable (grayed out)
- For 24-hour resources, all slots from 12 AM to 11:59 PM are available for booking
- Validation: Both start and end must be within resource's operating hours (unless 24-hour operation)

**Conflict Check:**
- Must not overlap with existing 'approved' or 'pending' bookings
- Checked before booking creation
- Returns list of conflicting bookings if found

### 8.4 Review Validation

**Resource ID:**
- Required: Yes
- Type: Integer
- Validation: Must exist in resources table

**Reviewer ID:**
- Required: Yes
- Type: Integer
- Validation: Must match authenticated user
- Must exist in users table

**Rating:**
- Required: Yes
- Type: Integer
- Range: 1-5 (inclusive)
- Must be whole number

**Comment:**
- Required: No
- Length: Max 2000 characters
- Sanitization: HTML/script tags removed

**Booking ID:**
- Required: No
- Type: Integer
- Validation: If provided, must be completed booking (status 'completed' or past end_datetime) by reviewer for this resource
- Optional link to completed booking
- Used to verify review eligibility (reviewer must have completed a booking for the resource)

**Uniqueness:**
- One review per user per resource enforced at database level
- UNIQUE constraint: (resource_id, reviewer_id)

**Update Window:**
- Reviews can be updated within 30 days of creation
- After 30 days, updates are blocked

### 8.5 Message Validation

**Receiver ID:**
- Required: Yes
- Type: Integer
- Validation: Must exist in users table
- Cannot be same as sender_id

**Content:**
- Required: Yes
- Length: 1-2000 characters
- Sanitization: HTML/script tags removed

**Rate Limiting:**
- Max 30 messages per user per minute
- Spam detection: Detect repeated identical messages

### 8.6 Admin Action Validation

**User ID (for suspend/role change/delete):**
- Required: Yes
- Type: Integer
- Validation: Must exist in users table

**New Role:**
- Required: Yes (for role change)
- Allowed values: 'student', 'staff', 'admin'
- Validation: Role change constraints (see Business Rules)

**Suspension Reason:**
- Required: Yes (for suspend)
- Length: 1-500 characters
- Required when suspending

**Action Type:**
- Required: Yes (for logging)
- Length: Max 100 characters
- Examples: 'suspend_user', 'change_role', 'delete_user'

---

## 9. Security Requirements

### 9.1 Input Validation

**Server-Side Validation:**
- All inputs validated on server (never trust client-side validation)
- Validation occurs in service layer before database operations
- Type checking, length validation, format validation
- Return specific error messages for validation failures

**Input Sanitization:**
- All text inputs sanitized to prevent XSS
- HTML tags and script tags removed or escaped
- Use `html.escape()` for output
- Template engine auto-escaping enabled

### 9.2 SQL Injection Prevention

**Parameterized Queries:**
- All SQL queries use parameterized statements
- Never concatenate user input into SQL strings
- Use `?` placeholders in SQL queries
- Pass parameters as tuple/list to cursor.execute()

**Example:**
```python
# CORRECT:
cursor.execute("SELECT * FROM users WHERE email = ?", (email,))

# WRONG:
cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
```

### 9.3 XSS (Cross-Site Scripting) Prevention

**Template Escaping:**
- Jinja2 auto-escaping enabled
- All user-generated content escaped in templates
- Use `{{ variable | escape }}` when needed
- HTML/script tags in user input are removed

**Content Sanitization:**
- Sanitize before storing in database
- Sanitize before displaying in templates
- Never render raw HTML from user input

### 9.4 CSRF (Cross-Site Request Forgery) Protection

**Flask-WTF Integration:**
- CSRF tokens required for all POST requests
- Form submissions include CSRF token
- Token validation on server side
- Use Flask-WTF for token generation and validation

### 9.5 Password Security

**Hashing:**
- Passwords hashed with bcrypt
- Salt rounds: 12
- Never store plaintext passwords
- Never log passwords
- Never return password_hash in API responses

**Password Complexity:**
- Minimum 8 characters
- Must contain uppercase, lowercase, number, special character
- Validated on registration and password change

### 9.6 Authentication & Authorization

**Session Management:**
- Flask-Login for session management
- Session tokens expire after 24 hours
- Secure session cookies (HttpOnly, Secure in production)
- Logout clears session

**Role-Based Access Control:**
- Roles: 'student', 'staff', 'admin'
- Access control checked on every protected route
- Admin routes require 'admin' role
- Resource owner permissions checked before edit/delete

**Authorization Checks:**
- User can only edit/delete their own resources
- User can only cancel their own bookings
- Staff/admin can approve bookings
- Admin can manage users and resources

### 9.7 File Upload Security

**File Type Restrictions:**
- Allowed types: Images only (JPG, PNG, GIF, WebP)
- File type validation based on extension and content
- MIME type checking

**File Size Limits:**
- Maximum file size: 16MB per file
- Configured in Flask: `MAX_CONTENT_LENGTH`

**Path Traversal Prevention:**
- Validate file paths
- Remove `..` and `/` from filenames
- Store files in designated uploads directory
- Never allow user-specified paths

### 9.8 Rate Limiting

**Registration:**
- Max 5 registration attempts per IP per hour

**Login:**
- Max 10 login attempts per IP per hour

**Messaging:**
- Max 30 messages per user per minute
- Spam detection for repeated identical messages

**Reviews:**
- Max 5 reviews per user per day

**Admin Actions:**
- Max 100 requests per hour per admin

### 9.9 Privacy & Data Protection

**Minimal PII Storage:**
- Store only necessary user information
- No sensitive personal data beyond name, email, department
- Admin can remove user data on request

**Password Policy:**
- Never return password_hash in responses
- Password reset not implemented in v1 (out of scope)

**Audit Logging:**
- All admin actions logged
- Logs include: admin_id, action, target, timestamp, details
- Logs are immutable (cannot be deleted)

---

## 10. User Interface Specifications

### 10.1 Homepage (`/`)

**Layout:**
- Header: Logo, navigation menu (Resources, Search, Messages, Admin if admin)
  - Header uses Indiana University crimson (#990000) background with cream/white text
- Hero section: Welcome message, main search box
  - Hero section uses cream (#EEEDEB or #F0EAD6) background
- Quick filters: Category buttons (Study Rooms, Lab Equipment, AV Equipment, Event Spaces, Tutoring)
  - Category buttons use crimson (#990000) for primary actions
- Featured resources: Grid display of top-rated or most-booked resources
  - Resource cards use cream backgrounds with crimson accents
- Footer: Copyright and links

**Key Elements:**
- Prominent search bar
- Category quick-access buttons (crimson primary buttons)
- "Get Started" CTA for new users (crimson button)
- Login/Register buttons in header (if not authenticated)

### 10.2 Resource Listing Page (`/resources/`)

**Layout:**
- Sidebar: Filter panel
  - Category filter (checkboxes)
  - Location filter (text input or dropdown)
  - Capacity range (min/max sliders or inputs)
  - Availability date/time picker
- Main content: Grid or list view of resources
- Pagination controls at bottom

**Resource Card Display:**
- Thumbnail image
- Title
- Location
- Capacity
- Category badge (crimson accent)
- Average rating (if available)
- "View Details" button (crimson primary button)
- Cards use cream (#EEEDEB or #F0EAD6) background with crimson (#990000) accents

**Functionality:**
- Search box at top
- Sort dropdown (Recent, Most Booked, Top Rated, Capacity)
- Filter reset button
- "Create Resource" button (if authenticated)

### 10.3 Resource Detail Page (`/resources/<id>`)

**Layout:**
- Top section:
  - Image carousel (if images available)
  - Title, location, category
  - Capacity and rating display
- Description section: Full description text
- Booking form:
  - Date/time picker for start time
  - Date/time picker for end time
  - "Request Booking" button
- Reviews section:
  - Average rating display
  - List of reviews with ratings and comments
  - "Write Review" button (if user has completed booking)

**Actions Available:**
- Book resource (if authenticated)
- Write review (if user has completed booking)
- Edit resource (if owner or admin)
- Delete resource (if owner or admin)

### 10.4 Booking Management

**My Bookings Page (`/bookings/`):**
- List of user's bookings
- Filter by status (pending, approved, rejected, cancelled)
- Booking card shows:
  - Resource title and thumbnail
  - Start/end datetime
  - Status badge
  - Actions (cancel, view details)
  - Approval/rejection actions (if owner/staff/admin)

**Booking Detail Page (`/bookings/<id>`):**
- Full booking information
- Resource details link
- Status information
- Action buttons based on user role and booking status

### 10.5 Admin Dashboard (`/admin/`)

**Layout:**
- Statistics cards:
  - Total Users (by role breakdown) - cards use cream background with crimson accents
  - Total Resources (by category and status) - cards use cream background with crimson accents
  - Total Bookings (by status) - cards use cream background with crimson accents
  - Total Reviews - cards use cream background with crimson accents
- Management sections:
  - User Management link (crimson buttons)
  - Resource Oversight
  - Admin Logs link

**User Management Page (`/admin/users`):**
- Table of all users
- Filters: Role, Suspended status, Department
- Search: Name or email
- Actions per user: Suspend, Change Role, Edit, Delete (soft delete)
- Pagination

**Resource Management Page (`/admin/resources`):**
- Table of all resources
- Comprehensive filtering options:
  - Status (draft, published, archived)
  - Category (study_room, lab_equipment, av_equipment, event_space, tutoring, other)
  - Featured status (featured, not featured)
  - Location (dropdown with unique locations)
  - Owner (dropdown with resource owners)
  - Keyword search (title or description)
- Actions per resource:
  - View resource details
  - Edit resource (admins can edit all resources)
  - Feature/Unfeature for homepage
  - Archive/Unarchive
  - **Reassign Ownership** (admin-only): Transfer ownership to another user
    - Available for all resources regardless of status or owner deletion status
    - Shows current owner information before reassignment
    - New owner gains full owner privileges (edit, publish, archive, etc.)
    - Action logged in admin logs for audit trail
- Pagination with filter preservation
- Visual indicators for resources owned by deleted users

**Admin Logs Page (`/admin/logs`):**
- Table of admin actions
- Filters: Admin ID, Action type
- Columns: Timestamp, Admin, Action, Target, Details
- Pagination

### 10.6 Messaging Interface

**Inbox (`/messages/`):**
- List of message threads
- Sorted by most recent message
- Shows: Other user's name, last message preview, unread count
- Click to view thread

**Thread View (`/messages/thread/<id>`):**
- Chronological list of messages
- Shows: Sender name, message content, timestamp
- Reply form at bottom
- Mark as read on view

### 10.7 AI Concierge Interface (`/ai/concierge`)

**Layout:**
- Query input box (natural language)
- Submit button
- Results section:
  - Resource recommendations
  - Natural language response
  - Links to resource details

**Functionality:**
- Accept natural language queries
- Parse query to extract search parameters
- Return relevant resources
- Provide summary statistics on request

### 10.8 Design Requirements

**Color Scheme & Branding:**
- **Primary Color (Crimson):** #990000
  - Used for primary buttons, links, headings, navigation highlights
  - Indiana University official crimson
- **Secondary Color (White):** #FFFFFF
  - Used for backgrounds, text contrast, card backgrounds
- **Background:** Light theme with white and light gray backgrounds (#f8f9fa)
- **UI Theme:** Clean, modern design with Bootstrap 5 framework
  - Subtle shadows and hover effects on cards and buttons
  - System font stack for consistent typography
  - Responsive design with modern UX patterns
- **Color Usage:**
  - Crimson for primary actions, active states, important information
  - White for page backgrounds and card backgrounds
  - Dark gray (#333333 or #212529) for primary text on light backgrounds
  - Ensure color contrast ratios meet WCAG 2.1 Level AA standards
- **Brand Consistency:**
  - Header/navigation uses crimson background with white text
  - Primary CTA buttons use crimson
  - Cards and content areas use white backgrounds with subtle shadows
  - Consistent spacing and typography throughout

**Responsive Design:**
- Mobile-first approach
- Breakpoints: Mobile (< 768px), Tablet (768px - 992px), Desktop (> 992px)
- Bootstrap 5 grid system

**Accessibility:**
- Semantic HTML elements
- ARIA labels for form inputs
- Keyboard navigation support
- Proper heading hierarchy (h1, h2, h3)
- Color contrast ratios (WCAG 2.1 Level AA) - verified with Indiana University colors
- Alt text for images

**UI Framework:**
- Bootstrap 5 for layout and components
- Bootstrap Icons for icons
- Custom CSS for Indiana University branding and color scheme
- Override Bootstrap default colors with IU crimson and white palette
- **UI Standardization:**
  - All filter/sort boxes use consistent styling across all pages
  - Form inputs standardized: `form-control-sm` and `form-select-sm` for uniform heights
  - Button standardization: Apply and Reset buttons have consistent height (`py-2`), width (side-by-side use `flex-fill`, separate columns use `w-100`), and font size (`0.875rem`)
  - Label standardization: All labels use consistent margin (`mb-1`), font size (`0.875rem`), and font weight (`fw-semibold`)
  - Consistent spacing and alignment throughout filter/sort interfaces for improved usability

---

## 11. AI Feature Specifications

### 11.1 AI Resource Concierge

**Purpose:**
A context-aware assistant that answers natural-language questions about available campus resources using project data and context files.

**Interface:**
- Natural language query input
- Real-time or on-demand processing
- Response in natural language with resource recommendations

**Context Grounding:**
- Loads context files from `/docs/context/` directories:
  - `/docs/context/APA/` - Agility, Processes & Automation artifacts
  - `/docs/context/DT/` - Design Thinking artifacts (personas, journey maps)
  - `/docs/context/PM/` - Product Management materials (PRDs, OKRs)
  - `/docs/context/shared/` - Common context files
- References PRD for product understanding
- Uses context to inform responses and recommendations

**Query Processing:**
1. Parse natural language query
2. Extract search parameters:
   - Category keywords
   - Capacity requirements
   - Location keywords
   - Time/availability preferences
   - General keywords
3. Execute search with extracted parameters
4. Enrich results with rating information
5. Generate natural language response
6. Include links to resource details

**Response Format:**
- Natural language summary
- Resource recommendations with details
- Links to full resource pages
- Summary statistics when requested

**Validation Requirements:**
- All responses must be based on actual database content
- Never fabricate resource information
- Never return unverifiable data
- All resource recommendations must exist in database
- Must include test verifying AI outputs behave predictably

**Implementation Notes:**
- Simple NLP parsing (keyword matching, regex patterns)
- Production system would use NLP libraries (spaCy, NLTK)
- Context files loaded at startup or on-demand
- Database queries use parameterized statements

**Example Queries:**
- "Find me a study room for 4 people"
- "What lab equipment is available?"
- "Show me event spaces in the library"
- "What are the most popular resources?"

### 11.2 AI Scheduler (Optional Enhancement)

**Purpose:**
An intelligent assistant that suggests optimal booking times and helps resolve conflicts.

**Functionality:**
- Analyze historical booking patterns
- Suggest optimal booking times based on:
  - Resource availability patterns
  - Historical usage data
  - User preferences
  - Peak usage avoidance
- Provide conflict resolution suggestions
- Recommend alternative resources when preferred time is unavailable
- Learn from user booking patterns over time

**Implementation:**
- Query database for historical booking data
- Calculate availability patterns (peak times, low-usage times)
- Machine learning or rule-based algorithms for suggestions
- Return time slot recommendations with confidence scores

**API Endpoint:**
```
GET /ai/scheduler?resource_id=<id>&preferred_date=<date>
Response: {
  'success': True,
  'recommendations': [
    {
      'start_datetime': '2025-12-15T10:00:00',
      'end_datetime': '2025-12-15T12:00:00',
      'confidence': 0.85,
      'reason': 'Low usage period, 95% availability'
    },
    ...
  ]
}
```

### 11.3 Auto-Summary Reporter (Optional Enhancement)

**Purpose:**
Generate automated weekly/monthly summaries and insights for administrators.

**Functionality:**
- Generate weekly/monthly reports automatically
- Summarize system usage statistics
- Identify top resources, trends, and patterns
- Generate natural language summaries
- Send reports via email or in-app notification

**Report Types:**
- "Top 5 Most Reserved Resources"
- "Peak Booking Times This Week"
- "Most Active Users"
- "Department Utilization Report"
- "Booking Trends Analysis"

**Implementation:**
- Scheduled task (cron job or Flask-APScheduler)
- Query database for statistics
- Generate natural language summaries using AI
- Format as email or dashboard display
- Archive reports for historical tracking

---

### 12.1 Unit Tests

**Booking Logic:**
- Conflict detection algorithm tests
- Various overlap scenarios
- Edge cases (exact overlaps, adjacent bookings)
- Status transition validation

**Data Access Layer:**
- At least one test verifying CRUD operations independently from Flask routes
- Test create, read, update, delete for resources
- Test database connection management

**Authentication:**
- Password hashing/verification
- Email validation edge cases
- SQL injection attempt tests
- Duplicate email registration

**Validation:**
- Input validation rules
- Edge cases (empty strings, special characters, boundary values)

### 12.2 Integration Tests

**Authentication Flow:**
- Register → Login → Access protected route
- Login → Logout → Access denied
- Session persistence

**Booking Flow:**
- Create resource → Book resource → Approve booking
- Conflict detection integration
- Status transition flow

**User Management:**
- Admin suspend user → User cannot login
- Role change → Access updated
- User deletion → Cascade effects

### 12.3 End-to-End Tests

**Booking Scenario:**
- User searches for resource
- User views resource details
- User creates booking request
- Owner approves booking
- User cancels booking
- User writes review

**Admin Scenario:**
- Admin logs in
- Admin views dashboard statistics
- Admin suspends user
- Admin views logs

### 12.4 Security Tests

**SQL Injection:**
- Attempt SQL injection in search queries
- Attempt SQL injection in form inputs
- Verify parameterized queries prevent injection

**XSS Prevention:**
- Attempt script injection in user input
- Verify output is escaped in templates
- Test HTML tag removal

**Authorization:**
- Test unauthorized access attempts
- Test role-based access control
- Test resource ownership checks

### 12.5 AI Feature Tests

**AI Concierge Validation:**
- Test natural language query parsing
- Test resource recommendations are factual
- Test context file loading
- Test response validation (no fabricated data)
- Test query with no results handled gracefully

**AI Scheduler Tests (if implemented):**
- Test recommendation algorithm accuracy
- Test conflict resolution suggestions
- Test time slot recommendation logic
- Test alternative resource suggestions

**Auto-Summary Reporter Tests (if implemented):**
- Test report generation accuracy
- Test summary content validation
- Test scheduled task execution
- Test report formatting

**Test Location:**
- Tests in `/tests/` directory
- AI feature tests in `/tests/ai_eval/` directory

**Test Framework:**
- pytest for test execution
- pytest-cov for coverage reporting
- Flask test client for route testing

### 12.6 Optional Feature Tests

**Calendar Integration Tests (if implemented):**
- Test Google Calendar OAuth flow
- Test iCal export format
- Test calendar sync functionality
- Test token refresh mechanism

**Waitlist Tests (if implemented):**
- Test waitlist queue management
- Test notification system
- Test priority handling
- Test expiration logic

**Analytics Tests (if implemented):**
- Test report generation accuracy
- Test data aggregation correctness
- Test access control for reports
- Test export format validation

**Semantic Search Tests (if implemented):**
- Test embedding generation
- Test similarity calculation
- Test hybrid search combination
- Test result relevance scoring

---

## 13. Technology Stack

### 13.1 Backend

**Framework:**
- Flask 2.3.0+ (Python web framework)
- Flask-Login 0.6.3+ (session management)
- Flask-WTF 1.2.0+ (CSRF protection, form handling)

**Python Version:**
- Python 3.10+ required

**Database:**
- SQLite for local development
- PostgreSQL optional for deployment

**Authentication:**
- bcrypt 4.0.0+ (password hashing, 12 salt rounds)
- PyJWT 2.8.0+ (optional, for API tokens)

**Data Validation:**
- WTForms 3.1.0+ (form validation)
- python-dateutil 2.8.0+ (datetime handling)

### 13.2 Frontend

**Templating:**
- Jinja2 (included with Flask)
- Auto-escaping enabled

**CSS Framework:**
- Bootstrap 5 (responsive UI)
- Bootstrap Icons (icon set)
- Custom CSS for Indiana University brand colors:
  - Primary (Crimson): #990000
  - Secondary (Cream): #EEEDEB or #F0EAD6
  - Custom CSS overrides Bootstrap default colors with IU palette

**JavaScript:**
- Vanilla JavaScript (minimal, for form enhancements)
- No jQuery required

### 13.3 Development Tools

**Testing:**
- pytest 7.4.0+
- pytest-cov 4.1.0+ (coverage reporting)

**Environment:**
- python-dotenv 1.0.0+ (environment variables)

**Version Control:**
- Git (required)
- GitHub (for repository hosting)

### 13.5 Optional Dependencies

**Calendar Integration:**
- google-auth 2.23.0+ (Google OAuth authentication)
- google-api-python-client 2.100.0+ (Google Calendar API)
- icalendar 5.0+ (iCal file generation)

**Waitlist Features:**
- No additional dependencies beyond core stack

**Analytics & Reporting:**
- Chart.js 4.0+ or Plotly 5.0+ (for visualizations)
- pandas 2.0+ (optional, for data analysis)
- Flask-APScheduler 1.13.0+ (for scheduled reports)

**Semantic Search:**
- sentence-transformers 2.2.0+ (for text embeddings)
- numpy 1.24.0+ (for vector operations)
- faiss-cpu 1.7.4+ (optional, for approximate nearest neighbor search)

**Performance & Caching:**
- Redis 4.5.0+ (optional, for caching)
- Flask-Caching 2.0.0+ (for Flask caching integration)

**Security Enhancements:**
- Flask-Limiter 3.0.0+ (for rate limiting)

**WebSocket Support (Optional):**
- Flask-SocketIO 5.3.0+ (for real-time features)
- python-socketio 5.9.0+ (Socket.IO client)

**Accessibility Testing:**
- axe-core (via npm, for automated accessibility testing)

### 13.4 Deployment (Optional)

**Platforms:**
- Heroku
- AWS Elastic Beanstalk
- DigitalOcean App Platform
- Any Python-compatible hosting

**Requirements:**
- Python 3.10+
- PostgreSQL (optional, SQLite for small deployments)
- Gunicorn or similar WSGI server

---

## 14. Deployment & Operations

### 14.1 Database Initialization

**Script:** `init_db.py`

**Functionality:**
- Creates all tables with proper schema
- Creates indexes for performance
- Creates default admin user:
  - Email: `admin@example.com`
  - Password: `Admin123!`
  - Role: `admin`
- Prints confirmation message

**Usage:**
```bash
python init_db.py
```

### 14.2 Environment Configuration

**Required Environment Variables:**
- `SECRET_KEY` - Flask secret key for sessions (default: 'dev-secret-key-change-in-production')
- `DATABASE_PATH` - Path to SQLite database (default: 'campus_resource_hub.db')
- `UPLOAD_FOLDER` - Path to uploads directory (default: 'uploads/')

**Configuration:**
- Load from `.env` file using python-dotenv
- Provide sensible defaults for development
- Document all required variables in README

### 14.3 File Structure Requirements

**Required Directories:**
- `uploads/` - User-uploaded files (created on startup if missing)
- `.prompt/` - AI development notes
- `docs/context/` - Context files for AI features

### 14.4 Default Admin Account

**Created on Database Initialization:**
- Email: `admin@example.com`
- Password: `Admin123!`
- Role: `admin`

**Security Note:**
- Must be changed immediately after first login in production
- Documented in README with warning

### 14.5 Running the Application

**Development:**
```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python init_db.py

# Run Flask development server
flask run
# Or: python app.py
```

**Production:**
```bash
# Use Gunicorn or similar WSGI server
gunicorn app:app
```

### 14.6 Maintenance Tasks

**Regular Tasks:**
- Backup database
- Review admin logs
- Monitor user activity
- Clean up old archived resources
- Review and moderate reviews

**Database Maintenance:**
- Vacuum SQLite database periodically
- Monitor database size
- Archive old data if needed

---

## 15. Optional Advanced Features (Top Projects)

The following optional features differentiate high-quality projects and should be implemented to create the best possible application:

### 15.1 Calendar Integration

**Google Calendar Sync:**
- OAuth 2.0 integration with Google Calendar API
- Automatic sync of approved bookings to user's Google Calendar
- Two-way sync (bookings in app appear in Google Calendar)
- Calendar event includes: resource title, location, start/end time, description
- OAuth token storage: Encrypted storage of user OAuth tokens
- Token refresh handling for expired tokens

**iCal Export:**
- Generate iCal (.ics) file for bookings
- Export single booking or multiple bookings
- Downloadable calendar file compatible with Outlook, Apple Calendar, etc.
- Recurring bookings support in iCal format
- Endpoint: `GET /bookings/export.ics?booking_id=<id>` or `GET /bookings/export.ics` (all user bookings)

**Implementation Notes:**
- Use `google-auth` and `google-api-python-client` libraries
- Use `icalendar` library for iCal generation
- Store OAuth credentials securely (environment variables)
- Handle OAuth callback flow
- Implement token refresh mechanism

### 15.2 Waitlist Functionality

**Requirements:**
- Allow users to join waitlist for fully booked resources
- Automatic notification when resource becomes available
- Priority queue system (first-come-first-served or priority-based)
- Waitlist management interface for resource owners

**Database Schema Addition:**
```sql
CREATE TABLE waitlist (
    waitlist_id INTEGER PRIMARY KEY AUTOINCREMENT,
    resource_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    requested_start_datetime DATETIME NOT NULL,
    requested_end_datetime DATETIME NOT NULL,
    priority INTEGER DEFAULT 0,  -- Higher number = higher priority
    status TEXT DEFAULT 'active' CHECK(status IN ('active', 'notified', 'fulfilled', 'cancelled')),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    notified_at DATETIME,
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id),
    FOREIGN KEY (user_id) REFERENCES users(user_id),
    UNIQUE(resource_id, user_id, requested_start_datetime, requested_end_datetime)
);
```

**Functionality:**
- User joins waitlist when booking fails due to conflicts
- When a booking is cancelled, check waitlist for matching time slots
- Notify first user in waitlist (email or in-app notification)
- User has time window (e.g., 24 hours) to confirm before moving to next user
- Waitlist entries expire after specified period (e.g., 30 days)
- Resource owner can view and manage waitlist for their resources

**Waitlist Management:**
- Sort by: priority, created_at (first-come-first-served), requested time
- Manual promotion by resource owner
- Automatic cleanup of expired entries

### 15.3 Role-Based Analytics & Reporting

**Requirements:**
- Department-specific usage reports
- Resource type analytics
- User activity reports
- Booking patterns analysis
- Peak usage times visualization

**Analytics Dashboard:**
- **Department Reports:**
  - Bookings by department
  - Resource utilization by department
  - Popular resources by department
  - User activity by department
  
- **Resource Type Analytics:**
  - Bookings by category (study_room, lab_equipment, etc.)
  - Average booking duration by category
  - Peak booking times by category
  - Revenue/usage metrics (if applicable)
  
- **User Activity Reports:**
  - Most active users
  - Booking frequency patterns
  - Review submission rates
  - Cancellation rates by user type
  
- **Booking Patterns:**
  - Peak booking times (hour, day of week)
  - Seasonal trends
  - Booking duration distribution
  - Conflict frequency by resource type
  
**Visualization Components:**
- Chart.js or similar for graphs and charts
- Bar charts for category/type breakdowns
- Line charts for time-series data
- Pie charts for distribution analysis
- Calendar heatmap for booking frequency

**Access Control:**
- Department reports visible to department heads/staff
- System-wide analytics visible to admins only
- Users can view their own activity reports

### 15.4 Advanced Search with Embedding Retrieval

**Requirements:**
- Semantic search using text embeddings
- Similarity-based resource matching
- Natural language query understanding
- Context-aware search results

**Implementation Approach:**
- Use sentence transformers (e.g., `sentence-transformers` library)
- Generate embeddings for resource titles and descriptions
- Store embeddings in database (vector storage) or external vector DB
- Query embedding generation from search terms
- Cosine similarity calculation for matching
- Hybrid search: Combine keyword search with semantic search

**Database Schema Addition:**
```sql
-- Add embedding column to resources table
ALTER TABLE resources ADD COLUMN title_embedding BLOB;
ALTER TABLE resources ADD COLUMN description_embedding BLOB;

-- Or use separate embedding table for scalability
CREATE TABLE resource_embeddings (
    resource_id INTEGER PRIMARY KEY,
    title_embedding BLOB NOT NULL,
    description_embedding BLOB,
    FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
);
```

**Search Algorithm:**
1. Generate embedding for user query
2. Calculate cosine similarity with all resource embeddings
3. Rank results by similarity score
4. Combine with keyword search results (weighted combination)
5. Return top N most relevant resources

**Performance Considerations:**
- Cache embeddings (recalculate only when resource updated)
- Use approximate nearest neighbor search for large datasets (e.g., FAISS)
- Index embeddings for faster retrieval
- Limit embedding dimensions for performance (e.g., 384 or 768 dimensions)

### 15.5 Enhanced AI Features

**AI Scheduler:**
- Suggest optimal booking times based on:
  - Historical usage patterns
  - User preferences
  - Resource availability patterns
  - Peak usage avoidance
- Conflict resolution suggestions
- Smart booking recommendations

**Auto-Summary Reporter:**
- Generate automated weekly/monthly summaries
- "Top 5 Most Reserved Resources" reports
- System insights and trends
- Usage statistics summaries
- Email or in-app notification delivery

**Enhanced Resource Concierge:**
- Multi-turn conversation support
- Booking assistance (help users create bookings)
- Personalized recommendations based on user history
- Context-aware follow-up questions

### 15.6 Accessibility Improvements & WCAG Conformance

**WCAG 2.1 Level AA Requirements:**
- **Color Contrast:**
  - Text contrast ratio: 4.5:1 for normal text, 3:1 for large text
  - UI component contrast: 3:1 for interactive elements
  - Verify all Indiana University color combinations meet standards
  
- **Keyboard Navigation:**
  - All functionality available via keyboard
  - Logical tab order
  - Visible focus indicators
  - Skip navigation links
  
- **Screen Reader Support:**
  - Semantic HTML structure
  - ARIA labels and descriptions
  - ARIA live regions for dynamic content
  - Proper heading hierarchy
  
- **Alternative Text:**
  - All images have descriptive alt text
  - Decorative images marked appropriately
  - Complex images have detailed descriptions
  
- **Forms:**
  - Clear labels for all inputs
  - Error messages associated with inputs
  - Required field indicators
  - Help text for complex fields
  
- **Time-based Media:**
  - Captions for any video content
  - Transcripts available
  
- **Content Structure:**
  - Proper heading levels (h1-h6)
  - Lists used appropriately
  - Landmarks for page regions (header, nav, main, footer)

**Testing Tools:**
- WAVE (Web Accessibility Evaluation Tool)
- axe DevTools
- Lighthouse accessibility audit
- Manual keyboard navigation testing
- Screen reader testing (NVDA, JAWS, VoiceOver)

### 15.7 Performance Optimizations

**Database Optimizations:**
- Additional indexes for frequently queried fields
- Query optimization and analysis
- Connection pooling
- Database query caching for read-heavy operations

**Frontend Optimizations:**
- Image optimization and lazy loading
- CSS/JavaScript minification
- CDN for static assets
- Progressive Web App (PWA) features

**Caching Strategy:**
- Redis or in-memory caching for:
  - Frequently accessed resources
  - Search results
  - Filter options (categories, locations)
  - User sessions
  - API responses

**Pagination & Lazy Loading:**
- Implement infinite scroll for large lists
- Virtual scrolling for very long lists
- Optimized pagination queries

### 15.8 Enhanced Security Features

**Advanced Security Measures:**
- Rate limiting per endpoint (Flask-Limiter)
- IP-based rate limiting
- Account lockout after failed login attempts
- Two-factor authentication (2FA) support (optional)
- Session timeout configuration
- Secure cookie settings (Secure, HttpOnly, SameSite)
- Content Security Policy (CSP) headers
- Security headers (X-Frame-Options, X-Content-Type-Options)

**Audit Trail Enhancements:**
- Detailed logging of all security events
- Failed login attempt logging
- Suspicious activity detection
- Admin action audit with IP addresses
- Data access logging

### 15.9 Enhanced User Experience Features

**Real-time Updates:**
- WebSocket support for live messaging
- Real-time availability updates
- Live booking status changes
- Push notifications (if browser supports)

**User Preferences:**
- Notification preferences (email, in-app, both)
- Default search filters
- Favorite resources
- Booking reminders (email or in-app)
- Calendar view for bookings

**Enhanced Booking Experience:**
- Visual calendar picker (interactive calendar widget)
- Drag-and-drop time selection
- Booking confirmation with calendar integration
- Booking modification workflow
- Booking history with filters

**Enhanced Messaging:**
- Rich text formatting support
- File attachments (with size limits)
- Message search functionality
- Message archiving
- Read receipts

### 15.10 Enhanced Admin Features

**Advanced Moderation Tools:**
- Bulk operations (suspend multiple users, archive multiple resources)
- Content moderation queue
- Flagged content review
- Automated spam detection
- User activity monitoring dashboard

**System Health Monitoring:**
- Database size monitoring
- Performance metrics
- Error rate tracking
- User activity metrics
- System alerts for critical issues

**Data Export:**
- Export user data (CSV, JSON)
- Export booking history
- Export reports (analytics data)
- GDPR-compliant data export

---

## 16. Non-Goals (Out of Scope for MVP)

The following features are explicitly **out of scope** for the MVP version (but may be implemented as optional enhancements):

- **Real-time Push Notifications:** WebSocket-based push notifications (optional enhancement)
- **Payment Processing:** No payment integration required
- **Mobile Native Apps:** Web-only application (responsive design sufficient)
- **Multi-language Support:** English only in MVP (i18n can be added as enhancement)
- **OAuth Authentication:** Email/password only in MVP (social login optional)
- **Video Conferencing Integration:** No Zoom/Teams integration
- **Resource Tracking Hardware:** No IoT device integration for resource tracking

**Note:** Email notifications or simulated notifications for booking confirmations and changes are **in scope** (as specified in the assignment brief). These may be simulated/logged rather than actually sent via email service.

---

## 17. Success Metrics

### 17.1 Adoption Metrics

- Number of registered users within first month
- Number of resources listed
- Booking completion rate (requests that result in approved bookings)
- Waitlist signups (if implemented)
- Calendar sync adoption rate (if implemented)

### 17.2 Engagement Metrics

- Average bookings per user
- Search-to-booking conversion rate
- Review submission rate (reviews per completed booking)
- Message thread activity
- AI Concierge usage rate

### 17.3 Quality Metrics

- Average resource rating (target: > 4.0)
- Booking conflict rate (target: < 5%)
- System uptime (target: > 99%)
- Average response time (target: < 500ms)
- Search result relevance (if semantic search implemented)

### 17.4 Technical Metrics

- Test coverage (target: > 80%)
- Code quality (linting, documentation)
- Security audit results
- Performance benchmarks
- Accessibility score (WCAG 2.1 Level AA compliance)
- Lighthouse performance score (target: > 90)

---

## Appendix A: Complete File Structure

```
campus-resource-hub/
├── app.py
├── init_db.py
├── requirements.txt
├── README.md
├── .gitignore
├── .env (not in git)
├── .prompt/
│   ├── dev_notes.md
│   └── golden_prompts.md
├── docs/
│   ├── PRD.md
│   ├── PRD_COMPLETE.md (this file)
│   ├── ER_DIAGRAM.md
│   ├── WIREFRAMES.md
│   ├── DEMO_SCRIPT.md
│   ├── SUBMISSION_CHECKLIST.md
│   ├── COMPLETION_REPORT.md
│   └── context/
│       ├── APA/
│       ├── DT/
│       ├── PM/
│       └── shared/
├── src/
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── auth_controller.py
│   │   ├── resources_controller.py
│   │   ├── bookings_controller.py
│   │   ├── search_controller.py
│   │   ├── messages_controller.py
│   │   ├── reviews_controller.py
│   │   ├── admin_controller.py
│   │   └── ai_concierge_controller.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── views/
│   │   ├── base.html
│   │   ├── home.html
│   │   ├── auth/
│   │   ├── resources/
│   │   ├── bookings/
│   │   ├── messages/
│   │   ├── reviews/
│   │   ├── admin/
│   │   └── ai_concierge/
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── resource_service.py
│   │   ├── booking_service.py
│   │   ├── search_service.py
│   │   ├── messaging_service.py
│   │   ├── review_service.py
│   │   ├── admin_service.py
│   │   └── ai_concierge.py
│   ├── data_access/
│   │   ├── __init__.py
│   │   └── database.py
│   └── static/
│       ├── css/
│       ├── js/
│       └── images/
├── tests/
│   ├── test_functionality_summary.py
│   ├── test_app_integration.py
│   ├── test_data_access_layer.py
│   ├── ai_eval/
│   │   └── test_ai_concierge.py
│   └── optional/  # Optional feature tests
│       ├── test_calendar_integration.py
│       ├── test_waitlist.py
│       ├── test_analytics.py
│       └── test_semantic_search.py
├── uploads/
└── campus_resource_hub.db (not in git)

# Optional Feature Files (if implemented):
├── src/
│   ├── controllers/
│   │   ├── calendar_controller.py  # Calendar integration
│   │   ├── waitlist_controller.py  # Waitlist management
│   │   ├── analytics_controller.py  # Analytics & reporting
│   │   └── semantic_search_controller.py  # Advanced search
│   ├── services/
│   │   ├── calendar_service.py  # Google Calendar sync, iCal export
│   │   ├── waitlist_service.py  # Waitlist queue management
│   │   ├── analytics_service.py  # Report generation
│   │   ├── semantic_search_service.py  # Embedding-based search
│   │   ├── ai_scheduler_service.py  # AI scheduling suggestions
│   │   └── auto_summary_service.py  # Automated reports
│   └── views/
│       ├── calendar/  # Calendar integration templates
│       ├── waitlist/  # Waitlist templates
│       ├── analytics/  # Analytics dashboard templates
│       └── semantic_search/  # Advanced search templates
```

---

## Appendix B: Key Implementation Details

### B.1 Flask Application Setup

```python
from flask import Flask
from flask_login import LoginManager
import os
from pathlib import Path

# Initialize Flask app with custom template and static folders
app = Flask(__name__, template_folder='src/views', static_folder='src/static')

# Load configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DATABASE_PATH'] = str(Path(__file__).parent / 'campus_resource_hub.db')
app.config['UPLOAD_FOLDER'] = str(Path(__file__).parent / 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# Import and register blueprints
from src.controllers import (
    auth_bp, resources_bp, bookings_bp, search_bp,
    messages_bp, reviews_bp, admin_bp, ai_concierge_bp
)

app.register_blueprint(auth_bp)
app.register_blueprint(resources_bp)
app.register_blueprint(bookings_bp)
app.register_blueprint(search_bp)
app.register_blueprint(messages_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(ai_concierge_bp)

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """Load user object for Flask-Login session management."""
    from src.models.user import User
    return User.get(user_id)

# Custom Jinja2 filter
@app.template_filter('flatten')
def flatten_filter(items):
    """Flatten a nested iterable of numbers."""
    result = []
    for item in items:
        if isinstance(item, (list, tuple, dict)):
            if isinstance(item, dict):
                result.extend(item.values())
            else:
                result.extend(item)
        else:
            result.append(item)
    return result

# Root route
@app.route('/')
def index():
    """Homepage"""
    from flask import render_template
    return render_template('home.html')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    """404 error handler"""
    return {'error': 'Not found'}, 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler"""
    return {'error': 'Internal server error'}, 500

# Create uploads directory on startup if needed
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### B.2 User Model Implementation

**Flask-Login Integration:**
The User model must implement Flask-Login's `UserMixin` for session management.

```python
from flask_login import UserMixin
from src.data_access.database import get_db_connection
import bcrypt

class User(UserMixin):
    """User model with authentication support."""
    
    def __init__(self, user_id, name, email, password_hash, role, 
                 department=None, profile_image=None, created_at=None, 
                 suspended=False, suspended_reason=None, suspended_at=None):
        self.id = user_id  # Required by Flask-Login
        self.user_id = user_id
        self.name = name
        self.email = email
        self.password_hash = password_hash
        self.role = role
        self.department = department
        self.profile_image = profile_image
        self.created_at = created_at
        self.suspended = suspended
        self.suspended_reason = suspended_reason
        self.suspended_at = suspended_at
    
    @staticmethod
    def get(user_id):
        """Retrieve user by ID from database."""
        # Implementation using get_db_connection()
        # Must handle sqlite3.Row objects correctly
        # Check key existence before accessing row['key']
    
    @staticmethod
    def get_by_email(email):
        """Retrieve user by email from database."""
        # Implementation using get_db_connection()
    
    def check_password(self, password):
        """Verify password against stored hash."""
        return bcrypt.checkpw(password.encode('utf-8'), 
                            self.password_hash.encode('utf-8'))
    
    def is_active(self):
        """Check if user account is active (not suspended)."""
        return not self.suspended
    
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == 'admin'
    
    def is_staff(self):
        """Check if user has staff or admin role."""
        return self.role in ['staff', 'admin']
```

**Key Requirements:**
- Must inherit from `UserMixin` (provides default implementations)
- Must have `id` attribute (used by Flask-Login)
- Must implement `is_active()` method (returns `False` if suspended)
- Must handle `sqlite3.Row` objects correctly when reading from database
- Check key existence before accessing row keys (e.g., `if 'key' in row.keys()`)

### B.3 Database Connection Pattern

```python
from contextlib import contextmanager
import sqlite3

DATABASE_PATH = 'campus_resource_hub.db'  # Or from config

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # Return dict-like rows
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
```

**Usage Pattern:**
```python
with get_db_connection() as conn:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    row = cursor.fetchone()
    if row:
        # Access row['column_name']
        pass
```

### B.4 Service Response Format

All services return standardized format:

```python
# Success
{'success': True, 'data': {...}}

# Error
{'success': False, 'error': 'Error message'}
```

### B.5 Conflict Detection SQL

```python
query = """
    SELECT * FROM bookings 
    WHERE resource_id = ? 
    AND status IN ('pending', 'approved')
    AND ((start_datetime < ? AND end_datetime > ?) 
         OR (start_datetime < ? AND end_datetime > ?)
         OR (start_datetime >= ? AND end_datetime <= ?))
"""
# Note: Excludes 'cancelled', 'rejected', and 'completed' bookings
# Completed bookings are past their end time and no longer active
```

---

## Implementation Priority Guide

### Phase 1: Core MVP (Required)
1. User Management & Authentication
2. Resource CRUD Operations
3. Search & Filter (basic keyword search)
4. Booking System with Conflict Detection
5. Messaging System (basic threading)
6. Reviews & Ratings
7. Admin Dashboard (basic statistics)
8. AI Resource Concierge (required AI feature)

### Phase 2: Enhanced Core Features
1. Enhanced search with availability filtering
2. Booking status workflow (pending → approved → completed)
3. Enhanced admin statistics
4. Improved UI/UX with Indiana University branding
5. WCAG 2.1 Level AA accessibility compliance

### Phase 3: Optional Advanced Features (Top Projects)

**High Impact, Moderate Complexity:**
1. Waitlist Functionality
2. iCal Export (simpler than full Google Calendar sync)
3. Enhanced Analytics Dashboard
4. Improved Accessibility (WCAG conformance)

**High Impact, High Complexity:**
1. Google Calendar OAuth Integration
2. Semantic Search with Embeddings
3. AI Scheduler
4. Auto-Summary Reporter

**Moderate Impact, Moderate Complexity:**
1. Enhanced User Preferences
2. Advanced Admin Features
3. Performance Optimizations (caching)
4. Enhanced Security Features (rate limiting)

**Low Priority:**
1. WebSocket Support (real-time messaging)
2. Progressive Web App (PWA) features
3. Advanced caching strategies

### Implementation Recommendations

**For Best-in-Class Project:**
- Implement all Phase 1 features (required)
- Implement Phase 2 enhancements
- Select 2-3 high-impact optional features from Phase 3:
  - Waitlist Functionality (high user value)
  - Enhanced Analytics Dashboard (demonstrates data skills)
  - Google Calendar Integration OR Semantic Search (demonstrates integration/ML skills)
  - Comprehensive WCAG accessibility (demonstrates UX maturity)

**Development Order:**
1. Complete all required core features first
2. Ensure all core features are tested and working
3. Add optional features incrementally
4. Test each optional feature thoroughly before moving to next
5. Document optional feature implementations

**Team Allocation:**
- Core features: Entire team (parallel development where possible)
- Optional features: Assign based on team member interests/skills
- Testing: Continuous throughout all phases
- Documentation: Updated as features are added

---

## Document Status

**Version:** 3.0 (Complete with Optional Features)  
**Status:** Comprehensive Technical Specification  
**Last Updated:** Fall 2025  
**Purpose:** Complete reference for recreating the Indiana University Campus Resource Hub application from scratch, including all required core features and optional advanced features for top-quality projects.

**Key Additions in v3.0:**
- Complete optional features documentation (Section 15)
- Optional feature API endpoints (Section 5.9)
- Enhanced AI features (Section 11.2-11.3)
- Optional dependencies (Section 13.5)
- Optional feature tests (Section 12.6)
- Implementation priority guide (above)

This document provides all information needed to recreate the application from scratch, including:
- All required core features (8 features)
- All optional advanced features (10+ enhancements)
- Complete technical specifications
- Database schemas for optional features
- API endpoint specifications
- Testing requirements for all features
- Implementation guidance and priorities

When providing this document to an AI agent or developer, they will have everything needed to build a complete, production-quality Indiana University Campus Resource Hub application.

