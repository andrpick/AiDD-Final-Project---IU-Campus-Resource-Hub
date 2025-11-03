"""
Database access layer with connection management.
All database operations should go through this module.
"""
from contextlib import contextmanager
import sqlite3
import os
from src.utils.logging_config import get_logger
from src.utils.exceptions import DatabaseError

logger = get_logger(__name__)

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
    
    Raises:
        DatabaseError: If database connection or operation fails
    """
    db_path = get_database_path()
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Return dict-like rows
    except sqlite3.Error as e:
        logger.error(f"Failed to connect to database at {db_path}: {e}")
        raise DatabaseError(f"Database connection failed: {e}") from e
    
    try:
        yield conn
        conn.commit()
    except sqlite3.Error as e:
        logger.error(f"Database operation failed: {e}")
        conn.rollback()
        raise DatabaseError(f"Database operation failed: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error in database operation: {e}", exc_info=True)
        conn.rollback()
        raise DatabaseError(f"Unexpected database error: {e}") from e
    finally:
        conn.close()

