# API Documentation

## Indiana University Campus Resource Hub

This document provides API endpoint documentation for the Campus Resource Hub application. The application uses Flask with Jinja2 templates (traditional MVC pattern) for most routes, but follows RESTful conventions for endpoint structure.

> **Note:** For complete technical specifications including business rules, validation rules, and detailed endpoint descriptions, see [docs/context/PRD_COMPLETE.md](docs/context/PRD_COMPLETE.md).

---

## Base URL

All endpoints are relative to the application root (e.g., `http://localhost:5000`).

---

## Authentication

Most endpoints require authentication via Flask-Login session management. Users must be logged in to access protected routes.

**Authentication Endpoints:**
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `GET /auth/logout` - User logout

---

## CSRF Protection

All POST requests require a CSRF token. Include the token in forms:
```html
<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
```

---

## API Endpoints

### Authentication

#### Register User
- **Endpoint:** `POST /auth/register`
- **Auth Required:** No
- **Request Body (form-data):**
  ```
  name: string (required)
  email: string (required, unique)
  password: string (required, min 8 chars, complexity requirements)
  role: string (optional, default: 'student', values: 'student', 'staff')
  department: string (optional)
  csrf_token: string (required)
  ```
- **Response:** Redirects to login page on success, or re-renders form with error

#### Login
- **Endpoint:** `POST /auth/login`
- **Auth Required:** No
- **Request Body (form-data):**
  ```
  email: string (required)
  password: string (required)
  csrf_token: string (required)
  ```
- **Response:** Redirects to home page or next page on success

#### Logout
- **Endpoint:** `GET /auth/logout`
- **Auth Required:** Yes
- **Response:** Redirects to home page

---

### Resources

#### List Resources (Search)
- **Endpoint:** `GET /search`
- **Auth Required:** No
- **Query Parameters:**
  - `keyword`: string (optional) - Search keyword
  - `category`: string (optional) - Filter by category
  - `location`: string (optional) - Filter by location
  - `capacity_min`: integer (optional) - Minimum capacity
  - `capacity_max`: integer (optional) - Maximum capacity
  - `available_from`: datetime (optional) - Available from datetime
  - `available_to`: datetime (optional) - Available to datetime
  - `sort_by`: string (optional) - Sort field
  - `page`: integer (optional, default: 1) - Page number
  - `page_size`: integer (optional, default: 20, max: 100) - Results per page
- **Response:** HTML page with search results

#### Get Resource Details
- **Endpoint:** `GET /resources/<resource_id>`
- **Auth Required:** No
- **Response:** HTML page with resource details, calendar, and booking form

#### Create Resource
- **Endpoint:** `POST /resources/create`
- **Auth Required:** Yes
- **Request Body (form-data, multipart/form-data):**
  ```
  title: string (required, 5-200 chars)
  description: string (optional, max 5000 chars)
  category: string (required, values: 'study_room', 'lab_equipment', 'av_equipment', 'event_space', 'tutoring', 'other')
  location: string (required, max 200 chars)
  capacity: integer (optional, must be > 0 if provided)
  images: file[] (optional, max 10 images)
  operating_hours_start: string (required, 12-hour format)
  operating_hours_end: string (required, 12-hour format)
  is_24_hours: boolean (optional, default: false)
  csrf_token: string (required)
  ```
- **Response:** Redirects to resource detail page on success

#### Update Resource
- **Endpoint:** `POST /resources/<resource_id>/edit`
- **Auth Required:** Yes (owner or admin)
- **Request Body:** Same as Create Resource
- **Response:** Redirects to resource detail page on success

#### Archive Resource
- **Endpoint:** `POST /resources/<resource_id>/archive`
- **Auth Required:** Yes (owner or admin)
- **Request Body:**
  ```
  csrf_token: string (required)
  ```
- **Response:** Redirects to resource detail page

#### Unarchive Resource
- **Endpoint:** `POST /resources/<resource_id>/unarchive`
- **Auth Required:** Yes (owner or admin)
- **Request Body:**
  ```
  csrf_token: string (required)
  ```
- **Response:** Redirects to resource detail page

---

### Bookings

#### List User Bookings
- **Endpoint:** `GET /bookings`
- **Auth Required:** Yes
- **Query Parameters:**
  - `status`: string (optional) - Filter by status
  - `resource_id`: integer (optional) - Filter by resource
  - `section`: string (optional) - Filter by section ('upcoming', 'previous', 'canceled')
  - `page`: integer (optional, default: 1)
  - `page_size`: integer (optional, default: 25, max: 100)
- **Response:** HTML page with user's bookings

#### Get Booking Details
- **Endpoint:** `GET /bookings/<booking_id>`
- **Auth Required:** Yes (requester, owner, or admin)
- **Response:** HTML page with booking details

#### Create Booking
- **Endpoint:** `POST /bookings/create`
- **Auth Required:** Yes
- **Request Body (form-data):**
  ```
  resource_id: integer (required)
  start_datetime: datetime (required, ISO format, must be at least 1 hour in future)
  end_datetime: datetime (required, ISO format, must be after start_datetime)
  request_reason: string (optional) - Reason for booking request
  csrf_token: string (required)
  ```
- **Response:** Redirects to booking detail page on success
- **Validation:**
  - Duration: 29 minutes minimum, 8 hours maximum
  - Must be within resource operating hours (unless 24-hour operation)
  - No conflicts with existing approved bookings

#### Approve Booking
- **Endpoint:** `POST /bookings/<booking_id>/approve`
- **Auth Required:** Yes (resource owner or admin)
- **Request Body:**
  ```
  csrf_token: string (required)
  ```
- **Response:** Redirects to referrer page
- **Note:** Sends notification to requester

#### Deny Booking
- **Endpoint:** `POST /bookings/<booking_id>/deny`
- **Auth Required:** Yes (resource owner or admin)
- **Request Body:**
  ```
  rejection_reason: string (optional)
  csrf_token: string (required)
  ```
- **Response:** Redirects to referrer page
- **Note:** Sends notification to requester

#### Cancel Booking
- **Endpoint:** `POST /bookings/<booking_id>/cancel`
- **Auth Required:** Yes (requester or admin)
- **Request Body:**
  ```
  csrf_token: string (required)
  ```
- **Response:** Redirects to bookings list
- **Note:** Sends notification to requester

#### Check Conflicts
- **Endpoint:** `POST /bookings/check-conflicts`
- **Auth Required:** Yes
- **Request Body (JSON):**
  ```json
  {
    "resource_id": integer,
    "start_datetime": "ISO datetime string",
    "end_datetime": "ISO datetime string",
    "exclude_booking_id": integer (optional)
  }
  ```
- **Response (JSON):**
  ```json
  {
    "success": boolean,
    "has_conflicts": boolean,
    "conflicts": array (if conflicts exist)
  }
  ```

#### Export Calendar
- **Endpoint:** `GET /bookings/<booking_id>/calendar/<calendar_type>`
- **Auth Required:** Yes (requester or admin)
- **Path Parameters:**
  - `calendar_type`: string (values: 'google', 'outlook', 'ical')
- **Response:** Calendar file download or redirect to calendar service

---

### Messages

#### List Message Threads
- **Endpoint:** `GET /messages`
- **Auth Required:** Yes
- **Response:** HTML page with message threads

#### View Thread
- **Endpoint:** `GET /messages/thread/<thread_id>`
- **Auth Required:** Yes (participant)
- **Response:** HTML page with thread messages

#### Send Message
- **Endpoint:** `POST /messages/send`
- **Auth Required:** Yes
- **Request Body (form-data):**
  ```
  receiver_id: integer (required)
  content: string (required, 1-2000 chars)
  thread_id: integer (optional) - Existing thread ID
  resource_id: integer (optional) - Related resource
  csrf_token: string (required)
  ```
- **Response:** Redirects to thread page

#### Mark Thread Read
- **Endpoint:** `POST /messages/thread/<thread_id>/read`
- **Auth Required:** Yes (participant)
- **Request Body:**
  ```
  csrf_token: string (required)
  ```
- **Response:** Redirects to messages list

#### Mark Thread Unread
- **Endpoint:** `POST /messages/thread/<thread_id>/unread`
- **Auth Required:** Yes (participant)
- **Request Body:**
  ```
  csrf_token: string (required)
  ```
- **Response:** Redirects to messages list

---

### Reviews

#### List Resource Reviews
- **Endpoint:** `GET /reviews/resource/<resource_id>`
- **Auth Required:** No
- **Query Parameters:**
  - `page`: integer (optional, default: 1)
  - `limit`: integer (optional, default: 10)
- **Response:** HTML page with reviews

#### Create Review
- **Endpoint:** `POST /reviews/create`
- **Auth Required:** Yes
- **Request Body (form-data):**
  ```
  resource_id: integer (required)
  rating: integer (required, 1-5)
  comment: string (optional, max 2000 chars)
  booking_id: integer (optional) - Link to completed booking
  csrf_token: string (required)
  ```
- **Response:** Redirects to resource reviews page
- **Note:** User must have completed a booking for the resource

#### Delete Review
- **Endpoint:** `POST /reviews/<review_id>/delete`
- **Auth Required:** Yes (reviewer or admin)
- **Request Body:**
  ```
  resource_id: integer (required)
  csrf_token: string (required)
  ```
- **Response:** Redirects to resource reviews page

---

### Admin Endpoints

All admin endpoints require admin role.

#### Admin Dashboard
- **Endpoint:** `GET /admin`
- **Auth Required:** Yes (admin)
- **Response:** HTML page with admin dashboard and statistics

#### User Management
- **Endpoint:** `GET /admin/users`
- **Auth Required:** Yes (admin)
- **Query Parameters:**
  - `search`: string (optional) - Search by name or email
  - `role`: string (optional) - Filter by role
  - `status`: string (optional) - Filter by status ('active', 'suspended', 'deleted')
  - `show_deleted`: boolean (optional) - Include deleted users
- **Response:** HTML page with user list

#### Suspend User
- **Endpoint:** `POST /admin/users/<user_id>/suspend`
- **Auth Required:** Yes (admin)
- **Request Body:**
  ```
  reason: string (required, 1-500 chars)
  csrf_token: string (required)
  ```
- **Response:** Redirects to user management page

#### Change User Role
- **Endpoint:** `POST /admin/users/<user_id>/role`
- **Auth Required:** Yes (admin)
- **Request Body:**
  ```
  new_role: string (required, values: 'student', 'staff', 'admin')
  csrf_token: string (required)
  ```
- **Response:** Redirects to user management page

#### Delete User (Soft Delete)
- **Endpoint:** `POST /admin/users/<user_id>/delete`
- **Auth Required:** Yes (admin)
- **Request Body:**
  ```
  csrf_token: string (required)
  ```
- **Response:** Redirects to user management page
- **Note:** Performs soft delete, anonymizes PII, archives resources, cancels bookings

#### Resource Management
- **Endpoint:** `GET /admin/resources`
- **Auth Required:** Yes (admin)
- **Query Parameters:** Various filters (status, category, featured, location, owner, keyword)
- **Response:** HTML page with resource list

#### Feature Resource
- **Endpoint:** `POST /admin/resources/<resource_id>/feature`
- **Auth Required:** Yes (admin)
- **Request Body:**
  ```
  csrf_token: string (required)
  ```
- **Response:** Redirects to resource management page

#### Archive Resource (Admin)
- **Endpoint:** `POST /admin/resources/<resource_id>/archive`
- **Auth Required:** Yes (admin)
- **Request Body:**
  ```
  csrf_token: string (required)
  ```
- **Response:** Redirects to resource management page

#### Booking Management
- **Endpoint:** `GET /admin/bookings`
- **Auth Required:** Yes (admin)
- **Query Parameters:**
  - `status`: string (optional) - Filter by status
  - `resource_id`: integer (optional) - Filter by resource
  - `requester_id`: integer (optional) - Filter by requester
- **Response:** HTML page with booking list

#### Admin Logs
- **Endpoint:** `GET /admin/logs`
- **Auth Required:** Yes (admin)
- **Query Parameters:**
  - `admin_id`: integer (optional) - Filter by admin
  - `action`: string (optional) - Filter by action type
  - `target_table`: string (optional) - Filter by target table
- **Response:** HTML page with admin action logs

---

### AI Concierge

#### Chat Endpoint
- **Endpoint:** `POST /ai/chat`
- **Auth Required:** No
- **Request Body (JSON):**
  ```json
  {
    "message": "string (required)",
    "history": array (optional) - Conversation history
  }
  ```
- **Response (JSON):**
  ```json
  {
    "success": boolean,
    "response": "string - AI response text",
    "resources": array (optional) - Related resources
  }
  ```
- **Note:** Uses Google Gemini API if available, falls back to search-based responses

---

## Error Responses

Most endpoints return HTML pages with flash messages for errors. JSON endpoints return JSON error responses:

```json
{
  "success": false,
  "error": "Error message"
}
```

Common HTTP status codes:
- `200` - Success
- `302` - Redirect (for form submissions)
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

---

## Request/Response Examples

### Example: Create Booking

**Request:**
```
POST /bookings/create
Content-Type: application/x-www-form-urlencoded

resource_id=1&start_datetime=2025-12-15T10:00:00&end_datetime=2025-12-15T12:00:00&csrf_token=abc123...
```

**Response:** Redirects to `/bookings/123` (booking detail page)

### Example: Check Conflicts (JSON)

**Request:**
```
POST /bookings/check-conflicts
Content-Type: application/json

{
  "resource_id": 1,
  "start_datetime": "2025-12-15T10:00:00Z",
  "end_datetime": "2025-12-15T12:00:00Z"
}
```

**Response:**
```json
{
  "success": true,
  "has_conflicts": false,
  "conflicts": []
}
```

---

## Notes

- All datetime values should be in ISO 8601 format
- File uploads use `multipart/form-data` encoding
- Most endpoints return HTML pages (traditional MVC), not JSON
- JSON endpoints are available for AJAX requests (e.g., conflict checking, AI chat)
- All POST requests require CSRF token validation
- Authentication is handled via Flask-Login session cookies

For detailed validation rules, business logic, and complete endpoint specifications, see [docs/context/PRD_COMPLETE.md](docs/context/PRD_COMPLETE.md).

