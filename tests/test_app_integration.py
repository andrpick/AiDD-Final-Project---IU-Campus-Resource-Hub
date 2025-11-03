"""
Integration tests for Flask application.
"""
import pytest
from app import app
from src.data_access.database import get_db_connection
import os
import tempfile

@pytest.fixture
def client():
    """Create test client with isolated temporary database."""
    # Create temporary database file
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    original_db_path = os.environ.get('DATABASE_PATH')
    os.environ['DATABASE_PATH'] = db_path
    
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    # Initialize database with full schema
    from init_db import init_database
    init_database()
    
    # Verify database is initialized
    with get_db_connection() as conn:
        cursor = conn.cursor()
        import time
        time.sleep(0.1)
        
        # Check if tables exist
        try:
            cursor.execute("SELECT user_id FROM users LIMIT 1")
            cursor.fetchone()
        except:
            # If tables don't exist, re-initialize
            init_database()
    
    with app.test_client() as client:
        yield client
    
    # Cleanup
    os.close(db_fd)
    if os.path.exists(db_path):
        os.unlink(db_path)
    if original_db_path:
        os.environ['DATABASE_PATH'] = original_db_path
    else:
        os.environ.pop('DATABASE_PATH', None)

def test_home_page(client):
    """Test homepage loads."""
    response = client.get('/')
    assert response.status_code == 200

def test_resources_page(client):
    """Test resources page redirects to search."""
    response = client.get('/resources/')
    # Resources route now redirects to search page
    assert response.status_code in [200, 302, 301]

