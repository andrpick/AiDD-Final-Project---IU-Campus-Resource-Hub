"""
Authentication service with user registration, login, and validation.
"""
import bcrypt
import re
from src.data_access.database import get_db_connection
from src.models.user import User

def validate_email(email):
    """Validate email format."""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_password(password):
    """Validate password complexity."""
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, "Password is valid"

def validate_name(name):
    """Validate name format."""
    if len(name) < 2 or len(name) > 100:
        return False, "Name must be between 2 and 100 characters"
    
    # Allow letters, spaces, hyphens, apostrophes
    if not re.match(r"^[a-zA-Z\s\-']+$", name):
        return False, "Name can only contain letters, spaces, hyphens, and apostrophes"
    
    return True, "Name is valid"

def register_user(name, email, password, role='student', department=None):
    """Register a new user."""
    # Validate inputs
    name_valid, name_msg = validate_name(name)
    if not name_valid:
        return {'success': False, 'error': name_msg}
    
    if not validate_email(email):
        return {'success': False, 'error': 'Invalid email format'}
    
    password_valid, password_msg = validate_password(password)
    if not password_valid:
        return {'success': False, 'error': password_msg}
    
    if role not in ['student', 'staff', 'admin']:
        return {'success': False, 'error': 'Invalid role'}
    
    # Check if email already exists (excluding deleted users)
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE email = ? AND (deleted = 0 OR deleted IS NULL)", (email.lower(),))
        if cursor.fetchone():
            return {'success': False, 'error': 'Email already registered'}
        
        # Hash password
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
        
        # Insert user
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role, department)
            VALUES (?, ?, ?, ?, ?)
        """, (name, email.lower(), password_hash, role, department))
        
        user_id = cursor.lastrowid
    
    return {'success': True, 'data': {'user_id': user_id}}

def authenticate_user(email, password):
    """Authenticate user with email and password."""
    user = User.get_by_email(email)
    
    if not user:
        return {'success': False, 'error': 'Invalid email or password'}
    
    # Check if user is deleted
    if user.deleted:
        return {'success': False, 'error': 'Account has been deleted'}
    
    if user.suspended:
        return {'success': False, 'error': 'Account is suspended'}
    
    if not user.check_password(password):
        return {'success': False, 'error': 'Invalid email or password'}
    
    return {'success': True, 'data': user}

