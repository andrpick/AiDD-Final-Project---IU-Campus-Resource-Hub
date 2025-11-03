"""
Database access layer with connection management.
All database operations should go through this module.
"""
from contextlib import contextmanager
import sqlite3
import os

def get_database_path():
    """Get database path from environment variable (read dynamically)."""
    return os.environ.get('DATABASE_PATH', 'campus_resource_hub.db')

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Ensures proper transaction handling and connection cleanup.
    
    Usage:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
    """
    db_path = get_database_path()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row  # Return dict-like rows
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

