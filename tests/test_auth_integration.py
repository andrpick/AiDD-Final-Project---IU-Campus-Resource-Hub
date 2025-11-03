"""
Integration tests for authentication flow.
Tests complete flow: register → login → access protected route.
"""
import pytest
from app import app
from src.data_access.database import get_db_connection
import os
import tempfile


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
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing
    
    # Initialize test database - ensure it completes before tests run
    from init_db import init_database
    init_database()  # Uses DB_PATH from environment
    
    # Verify database is initialized
    with get_db_connection() as conn:
        cursor = conn.cursor()
        import time
        time.sleep(0.1)
        
        # Check if tables exist by querying admin user
        try:
            cursor.execute("SELECT user_id FROM users WHERE email = ?", ('admin@example.com',))
            admin = cursor.fetchone()
        except:
            # If tables don't exist, re-initialize
            init_database()
            cursor.execute("SELECT user_id FROM users WHERE email = ?", ('admin@example.com',))
            admin = cursor.fetchone()
    
    with app.test_client() as client:
        yield client
    
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


def test_register_new_user(client):
    """Test user registration."""
    response = client.post('/auth/register', data={
        'name': 'Test User',
        'email': 'testuser@example.com',
        'password': 'TestPass123!',
        'confirm_password': 'TestPass123!',
        'role': 'student'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    
    # Verify user was created in database
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", ('testuser@example.com',))
        user = cursor.fetchone()
        assert user is not None
        assert user['name'] == 'Test User'
        assert user['email'] == 'testuser@example.com'
        assert user['role'] == 'student'


def test_register_duplicate_email(client):
    """Test that duplicate email registration fails."""
    # Register first user
    client.post('/auth/register', data={
        'name': 'First User',
        'email': 'duplicate@example.com',
        'password': 'TestPass123!',
        'confirm_password': 'TestPass123!',
        'role': 'student'
    }, follow_redirects=True)
    
    # Try to register with same email
    response = client.post('/auth/register', data={
        'name': 'Second User',
        'email': 'duplicate@example.com',
        'password': 'TestPass123!',
        'confirm_password': 'TestPass123!',
        'role': 'student'
    }, follow_redirects=True)
    
    # Should fail (redirect with error or status code indicating failure)
    assert response.status_code in [200, 400]
    
    # Verify only one user exists
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users WHERE email = ?", ('duplicate@example.com',))
        count = cursor.fetchone()[0]
        assert count == 1


def test_login_success(client):
    """Test successful login."""
    # Register a user first
    client.post('/auth/register', data={
        'name': 'Login Test User',
        'email': 'login@example.com',
        'password': 'TestPass123!',
        'confirm_password': 'TestPass123!',
        'role': 'student'
    }, follow_redirects=True)
    
    # Login
    response = client.post('/auth/login', data={
        'email': 'login@example.com',
        'password': 'TestPass123!'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    # Should redirect to home or dashboard after login
    assert b'Logout' in response.data or b'My Bookings' in response.data or response.request.path == '/'


def test_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    # Register a user first
    client.post('/auth/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': 'TestPass123!',
        'confirm_password': 'TestPass123!',
        'role': 'student'
    }, follow_redirects=True)
    
    # Try to login with wrong password
    response = client.post('/auth/login', data={
        'email': 'test@example.com',
        'password': 'WrongPassword123!'
    }, follow_redirects=True)
    
    # Should remain on login page or show error
    assert response.status_code == 200
    # Should show error message or stay on login page
    assert b'Invalid' in response.data or b'incorrect' in response.data.lower() or b'Login' in response.data


def test_access_protected_route_while_logged_in(client):
    """Test accessing protected route after login."""
    # Register and login
    client.post('/auth/register', data={
        'name': 'Protected Route User',
        'email': 'protected@example.com',
        'password': 'TestPass123!',
        'confirm_password': 'TestPass123!',
        'role': 'student'
    }, follow_redirects=True)
    
    client.post('/auth/login', data={
        'email': 'protected@example.com',
        'password': 'TestPass123!'
    }, follow_redirects=True)
    
    # Access protected route (e.g., my bookings)
    response = client.get('/bookings/', follow_redirects=True)
    
    assert response.status_code == 200
    # Should see booking page content
    assert b'My Bookings' in response.data or b'Booking' in response.data or b'bookings' in response.data.lower()


def test_access_protected_route_without_login(client):
    """Test that protected routes redirect to login when not authenticated."""
    # Try to access protected route without logging in
    response = client.get('/bookings/', follow_redirects=True)
    
    # Should redirect to login page
    assert response.status_code == 200
    assert b'Login' in response.data or b'login' in response.data.lower()


def test_logout(client):
    """Test logout functionality."""
    # Register and login
    client.post('/auth/register', data={
        'name': 'Logout Test User',
        'email': 'logout@example.com',
        'password': 'TestPass123!',
        'confirm_password': 'TestPass123!',
        'role': 'student'
    }, follow_redirects=True)
    
    client.post('/auth/login', data={
        'email': 'logout@example.com',
        'password': 'TestPass123!'
    }, follow_redirects=True)
    
    # Logout
    response = client.get('/auth/logout', follow_redirects=True)
    
    assert response.status_code == 200
    # Should redirect to home or show login option
    assert b'Login' in response.data or b'login' in response.data.lower() or response.request.path == '/'
    
    # Verify cannot access protected route after logout
    response = client.get('/bookings/', follow_redirects=True)
    assert b'Login' in response.data or response.request.path == '/auth/login'


def test_complete_auth_flow(client):
    """Test complete authentication flow: register → login → access protected route → logout."""
    # Step 1: Register
    response = client.post('/auth/register', data={
        'name': 'Complete Flow User',
        'email': 'complete@example.com',
        'password': 'TestPass123!',
        'confirm_password': 'TestPass123!',
        'role': 'student'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # Step 2: Login
    response = client.post('/auth/login', data={
        'email': 'complete@example.com',
        'password': 'TestPass123!'
    }, follow_redirects=True)
    assert response.status_code == 200
    
    # Step 3: Access protected route (bookings)
    response = client.get('/bookings/', follow_redirects=True)
    assert response.status_code == 200
    assert b'Booking' in response.data or b'booking' in response.data.lower()
    
    # Step 4: Access another protected route (messages)
    response = client.get('/messages/', follow_redirects=True)
    assert response.status_code == 200
    
    # Step 5: Logout
    response = client.get('/auth/logout', follow_redirects=True)
    assert response.status_code == 200
    
    # Step 6: Verify cannot access protected route after logout
    response = client.get('/bookings/', follow_redirects=True)
    assert b'Login' in response.data or response.request.path == '/auth/login'

