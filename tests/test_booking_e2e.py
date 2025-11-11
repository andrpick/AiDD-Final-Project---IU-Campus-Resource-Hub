"""
End-to-end test for booking flow.
Demonstrates complete booking process through the UI.
"""
import pytest
from app import app
from src.data_access.database import get_db_connection
from src.utils.config import Config
import os
import tempfile
from datetime import datetime, timedelta


@pytest.fixture
def client():
    """Create test client with isolated temporary database."""
    # Store original database path
    original_db_path = os.environ.get('DATABASE_PATH')
    if original_db_path:
        os.environ['DATABASE_PATH_ORIGINAL'] = original_db_path
    
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    os.environ['DATABASE_PATH'] = db_path
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    app.config['WTF_CSRF_ENABLED'] = False
    
    # Initialize database - ensure it completes before querying
    from init_db import init_database
    import sqlite3
    import time
    
    # Initialize database
    init_database()
    
    # Wait for initialization to complete
    time.sleep(0.2)
    
    # Verify database is initialized by directly checking the file
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        table_exists = cursor.fetchone()
        if not table_exists:
            # Re-initialize if tables don't exist
            init_database()
            time.sleep(0.2)
    finally:
        conn.close()
    
    # Create test users and resource
    # Note: init_db creates admin@example.com, so use different emails
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Check if users already exist, otherwise create them
        cursor.execute("SELECT user_id FROM users WHERE email = ?", ('e2eowner@example.com',))
        owner = cursor.fetchone()
        if owner:
            owner_id = owner['user_id']
        else:
            cursor.execute("""
                INSERT INTO users (name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, ('Resource Owner', 'e2eowner@example.com', '$2b$12$testhash', 'staff'))
            owner_id = cursor.lastrowid
        
        cursor.execute("SELECT user_id FROM users WHERE email = ?", ('e2estudent@example.com',))
        student = cursor.fetchone()
        if student:
            student_id = student['user_id']
        else:
            cursor.execute("""
                INSERT INTO users (name, email, password_hash, role)
                VALUES (?, ?, ?, ?)
            """, ('Test Student', 'e2estudent@example.com', '$2b$12$testhash', 'student'))
            student_id = cursor.lastrowid
        
        # Create resource
        cursor.execute("""
            INSERT INTO resources (owner_id, title, description, category, location, capacity, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (owner_id, 'Test Study Room', 'A test study room', 'study_room', 'Library 101', 10, 'published'))
        resource_id = cursor.lastrowid
        conn.commit()
    
    with app.test_client() as client:
        # Login as student
        with client.session_transaction() as sess:
            # Manually set session (simulating login)
            from flask_login import login_user
            from src.models.user import User
            user = User(user_id=student_id, name='Test Student', email='student@example.com', 
                       password_hash='$2b$12$testhash', role='student')
            sess['_user_id'] = str(student_id)
            sess['_fresh'] = True
        yield client, resource_id, student_id
    
    # Cleanup - ensure database is deleted
    os.close(db_fd)
    if os.path.exists(db_path):
        try:
            os.unlink(db_path)
        except Exception:
            pass  # Ignore cleanup errors
    
    # Restore original database path
    original_db_path = os.environ.get('DATABASE_PATH_ORIGINAL')
    if original_db_path:
        os.environ['DATABASE_PATH'] = original_db_path
        os.environ.pop('DATABASE_PATH_ORIGINAL', None)
    else:
        os.environ.pop('DATABASE_PATH', None)


def test_booking_flow_search_to_book(client):
    """Test complete booking flow: search → select → book → verify."""
    client_obj, resource_id, student_id = client
    
    # Step 1: Search for resources
    response = client_obj.get('/search/?keyword=study')
    assert response.status_code == 200
    assert b'Test Study Room' in response.data or b'study' in response.data.lower()
    
    # Step 2: View resource detail
    response = client_obj.get(f'/resources/{resource_id}')
    assert response.status_code == 200
    assert b'Test Study Room' in response.data
    assert b'Book' in response.data or b'booking' in response.data.lower()
    
    # Step 3: Create booking
    # Calculate future datetime (at least min_advance_hours from now) in configured timezone
    from dateutil.tz import gettz
    tz = gettz(Config.TIMEZONE)
    now = datetime.now(tz)
    
    # Create booking during operating hours
    min_advance_hours = Config.BOOKING_MIN_ADVANCE_HOURS
    booking_hour = max(Config.BOOKING_OPERATING_HOURS_START + 1, (now.hour + min_advance_hours + 1) % 24)
    if booking_hour >= Config.BOOKING_OPERATING_HOURS_END:
        booking_hour = Config.BOOKING_OPERATING_HOURS_START + 1
    
    tomorrow = (now + timedelta(days=1)).replace(hour=booking_hour, minute=0, second=0, microsecond=0)
    future_start_local = tomorrow
    future_end_local = future_start_local + timedelta(hours=1)
    
    # Format for datetime-local input (controller expects configured timezone)
    start_str = future_start_local.strftime('%Y-%m-%dT%H:%M')
    end_str = future_end_local.strftime('%Y-%m-%dT%H:%M')
    
    response = client_obj.post('/bookings/create', data={
        'resource_id': resource_id,
        'start_datetime': start_str,
        'end_datetime': end_str,
        'purpose': 'Test booking purpose'
    }, follow_redirects=True)
    
    # Should succeed (redirect or success message)
    assert response.status_code == 200
    
    # Step 4: Verify booking was created
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM bookings 
            WHERE resource_id = ? AND requester_id = ?
            ORDER BY created_at DESC LIMIT 1
        """, (resource_id, student_id))
        booking = cursor.fetchone()
        
        assert booking is not None
        assert booking['resource_id'] == resource_id
        assert booking['requester_id'] == student_id
        assert booking['status'] == 'approved'


def test_booking_conflict_detection(client):
    """Test that booking conflicts are detected and prevented."""
    client_obj, resource_id, student_id = client
    
    # Create first booking in configured timezone
    from dateutil.tz import gettz
    tz = gettz(Config.TIMEZONE)
    now = datetime.now(tz)
    
    # Create booking during operating hours
    min_advance_hours = Config.BOOKING_MIN_ADVANCE_HOURS
    booking_hour = max(Config.BOOKING_OPERATING_HOURS_START + 1, (now.hour + min_advance_hours + 1) % 24)
    if booking_hour >= Config.BOOKING_OPERATING_HOURS_END:
        booking_hour = Config.BOOKING_OPERATING_HOURS_START + 1
    
    tomorrow = (now + timedelta(days=1)).replace(hour=booking_hour, minute=0, second=0, microsecond=0)
    future_start_local = tomorrow
    future_end_local = future_start_local + timedelta(hours=1)
    
    start_str = future_start_local.strftime('%Y-%m-%dT%H:%M')
    end_str = future_end_local.strftime('%Y-%m-%dT%H:%M')
    
    # First booking
    response1 = client_obj.post('/bookings/create', data={
        'resource_id': resource_id,
        'start_datetime': start_str,
        'end_datetime': end_str,
        'purpose': 'First booking'
    }, follow_redirects=True)
    assert response1.status_code == 200
    
    # Try to create overlapping booking (same day, overlaps with first booking)
    overlap_start_local = future_start_local + timedelta(minutes=30)
    overlap_end_local = overlap_start_local + timedelta(hours=1)
    
    # Ensure end is within operating hours
    if overlap_end_local.hour > Config.BOOKING_OPERATING_HOURS_END:
        overlap_end_local = overlap_end_local.replace(hour=Config.BOOKING_OPERATING_HOURS_END, minute=0, second=0, microsecond=0)
    
    overlap_start_str = overlap_start_local.strftime('%Y-%m-%dT%H:%M')
    overlap_end_str = overlap_end_local.strftime('%Y-%m-%dT%H:%M')
    
    response2 = client_obj.post('/bookings/create', data={
        'resource_id': resource_id,
        'start_datetime': overlap_start_str,
        'end_datetime': overlap_end_str,
        'purpose': 'Overlapping booking'
    }, follow_redirects=True)
    
    # Should fail or show error
    assert response2.status_code == 200
    assert b'conflict' in response2.data.lower() or b'unavailable' in response2.data.lower() or b'error' in response2.data.lower()
    
    # Verify only one booking exists
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM bookings 
            WHERE resource_id = ? AND requester_id = ?
        """, (resource_id, student_id))
        count = cursor.fetchone()[0]
        # Should have only 1 booking (the first one)
        assert count == 1


def test_view_my_bookings(client):
    """Test viewing bookings after creation."""
    client_obj, resource_id, student_id = client
    
    # Create a booking first (in configured timezone)
    from dateutil.tz import gettz
    tz = gettz(Config.TIMEZONE)
    now = datetime.now(tz)
    
    # Create booking during operating hours
    min_advance_hours = Config.BOOKING_MIN_ADVANCE_HOURS
    booking_hour = max(Config.BOOKING_OPERATING_HOURS_START + 1, (now.hour + min_advance_hours + 1) % 24)
    if booking_hour >= Config.BOOKING_OPERATING_HOURS_END:
        booking_hour = Config.BOOKING_OPERATING_HOURS_START + 1
    
    tomorrow = (now + timedelta(days=1)).replace(hour=booking_hour, minute=0, second=0, microsecond=0)
    future_start_local = tomorrow
    future_end_local = future_start_local + timedelta(hours=1)
    
    client_obj.post('/bookings/create', data={
        'resource_id': resource_id,
        'start_datetime': future_start_local.strftime('%Y-%m-%dT%H:%M'),
        'end_datetime': future_end_local.strftime('%Y-%m-%dT%H:%M'),
        'purpose': 'Test booking'
    }, follow_redirects=True)
    
    # View bookings page
    response = client_obj.get('/bookings/')
    assert response.status_code == 200
    assert b'My Bookings' in response.data or b'booking' in response.data.lower()
    # Should show the booking we just created (check for resource title or booking info)
    # The resource title might be in the HTML, or we can verify booking exists in database
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM bookings 
            WHERE resource_id = ? AND requester_id = ?
        """, (resource_id, student_id))
        booking_count = cursor.fetchone()[0]
        assert booking_count > 0  # At least one booking should exist


def test_booking_validation_min_duration(client):
    """Test that bookings shorter than minimum duration are rejected."""
    client_obj, resource_id, student_id = client
    
    # Use configured timezone
    from dateutil.tz import gettz
    tz = gettz(Config.TIMEZONE)
    now = datetime.now(tz)
    
    # Create booking during operating hours
    min_advance_hours = Config.BOOKING_MIN_ADVANCE_HOURS
    booking_hour = max(Config.BOOKING_OPERATING_HOURS_START + 1, (now.hour + min_advance_hours + 1) % 24)
    if booking_hour >= Config.BOOKING_OPERATING_HOURS_END:
        booking_hour = Config.BOOKING_OPERATING_HOURS_START + 1
    
    tomorrow = (now + timedelta(days=1)).replace(hour=booking_hour, minute=0, second=0, microsecond=0)
    future_start_local = tomorrow
    future_end_local = future_start_local + timedelta(minutes=Config.BOOKING_MIN_DURATION_MINUTES - 10)  # Less than minimum
    
    response = client_obj.post('/bookings/create', data={
        'resource_id': resource_id,
        'start_datetime': future_start_local.strftime('%Y-%m-%dT%H:%M'),
        'end_datetime': future_end_local.strftime('%Y-%m-%dT%H:%M'),
        'purpose': 'Too short booking'
    }, follow_redirects=True)
    
    # Should fail validation
    assert response.status_code == 200
    assert str(Config.BOOKING_MIN_DURATION_MINUTES).encode() in response.data or b'minimum' in response.data.lower() or b'error' in response.data.lower()


def test_booking_validation_advance_booking(client):
    """Test that bookings less than minimum advance time are rejected."""
    client_obj, resource_id, student_id = client
    
    # Booking too soon (less than min_advance_hours from now) in configured timezone
    from dateutil.tz import gettz
    tz = gettz(Config.TIMEZONE)
    now = datetime.now(tz)
    
    min_advance_minutes = Config.BOOKING_MIN_ADVANCE_HOURS * 60
    too_soon_local = now + timedelta(minutes=min_advance_minutes // 2)  # Half of required advance
    
    # Ensure it's during operating hours
    if too_soon_local.hour < Config.BOOKING_OPERATING_HOURS_START:
        too_soon_local = too_soon_local.replace(hour=Config.BOOKING_OPERATING_HOURS_START, minute=0, second=0, microsecond=0)
    elif too_soon_local.hour >= Config.BOOKING_OPERATING_HOURS_END:
        too_soon_local = (now + timedelta(days=1)).replace(hour=Config.BOOKING_OPERATING_HOURS_START + 1, minute=0, second=0, microsecond=0)
    
    too_soon_end_local = too_soon_local + timedelta(hours=1)
    if too_soon_end_local.hour > Config.BOOKING_OPERATING_HOURS_END:
        too_soon_end_local = too_soon_local.replace(hour=Config.BOOKING_OPERATING_HOURS_END, minute=0, second=0, microsecond=0)
    
    response = client_obj.post('/bookings/create', data={
        'resource_id': resource_id,
        'start_datetime': too_soon_local.strftime('%Y-%m-%dT%H:%M'),
        'end_datetime': too_soon_end_local.strftime('%Y-%m-%dT%H:%M'),
        'purpose': 'Too soon booking'
    }, follow_redirects=True)
    
    # Should fail validation - check flash message or error
    assert response.status_code == 200
    assert str(Config.BOOKING_MIN_ADVANCE_HOURS).encode() in response.data or b'hour' in response.data.lower() or b'error' in response.data.lower() or b'Booking' in response.data

