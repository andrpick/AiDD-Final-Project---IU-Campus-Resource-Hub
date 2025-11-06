"""
User model with Flask-Login integration.
"""
from flask_login import UserMixin
from src.data_access.database import get_db_connection

class User(UserMixin):
    """User model with authentication support."""
    
    def __init__(self, user_id, name, email, password_hash, role,
                 department=None, profile_image=None, created_at=None,
                 suspended=False, suspended_reason=None, suspended_at=None,
                 deleted=False, deleted_at=None, deleted_by=None):
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
        self.deleted = deleted
        self.deleted_at = deleted_at
        self.deleted_by = deleted_by
    
    @staticmethod
    def get(user_id):
        """Retrieve user by ID from database."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            
            if row:
                return User._from_row(row)
            return None
    
    @staticmethod
    def get_by_email(email):
        """Retrieve user by email from database (excluding deleted users)."""
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ? AND (deleted = 0 OR deleted IS NULL)", (email.lower(),))
            row = cursor.fetchone()
            
            if row:
                return User._from_row(row)
            return None
    
    @staticmethod
    def _from_row(row):
        """Create User object from database row."""
        # Handle sqlite3.Row object
        # sqlite3.Row objects don't have .get() method, use dictionary access
        user_id = row['user_id']
        name = row['name']
        email = row['email']
        password_hash = row['password_hash']
        role = row['role']
        
        # Use dictionary-style access for optional fields
        # sqlite3.Row supports 'key in row.keys()' check and row['key'] access
        row_keys = row.keys()
        department = row['department'] if 'department' in row_keys else None
        profile_image = row['profile_image'] if 'profile_image' in row_keys else None
        created_at = row['created_at'] if 'created_at' in row_keys else None
        suspended = bool(row['suspended']) if 'suspended' in row_keys else False
        suspended_reason = row['suspended_reason'] if 'suspended_reason' in row_keys else None
        suspended_at = row['suspended_at'] if 'suspended_at' in row_keys else None
        deleted = bool(row['deleted']) if 'deleted' in row_keys else False
        deleted_at = row['deleted_at'] if 'deleted_at' in row_keys else None
        deleted_by = row['deleted_by'] if 'deleted_by' in row_keys else None
        
        return User(
            user_id=user_id,
            name=name,
            email=email,
            password_hash=password_hash,
            role=role,
            department=department,
            profile_image=profile_image,
            created_at=created_at,
            suspended=suspended,
            suspended_reason=suspended_reason,
            suspended_at=suspended_at,
            deleted=deleted,
            deleted_at=deleted_at,
            deleted_by=deleted_by
        )
    
    def check_password(self, password):
        """Verify password against stored hash."""
        import bcrypt
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                self.password_hash.encode('utf-8')
            )
        except Exception:
            return False
    
    def is_active(self):
        """Check if user account is active (not suspended and not deleted)."""
        return not self.suspended and not self.deleted
    
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == 'admin'
    
    def is_staff(self):
        """Check if user has staff or admin role."""
        return self.role in ['staff', 'admin']

