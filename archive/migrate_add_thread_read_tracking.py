"""
Migration script to add thread_read table for tracking thread-level read/unread status.
This allows users to mark entire threads as read or unread independently of individual messages.
"""
import sqlite3
import os

# Database path
DB_PATH = os.environ.get('DATABASE_PATH', 'campus_resource_hub.db')

def migrate():
    """Add thread_read table for tracking thread-level read status."""
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Skipping migration.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if table already exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='thread_read'")
        if cursor.fetchone():
            print("Table thread_read already exists. Skipping migration.")
            return
        
        # Create thread_read table
        print("Creating thread_read table...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS thread_read (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                thread_id INTEGER NOT NULL,
                is_read BOOLEAN DEFAULT 1,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                UNIQUE(user_id, thread_id)
            )
        """)
        
        conn.commit()
        print("Successfully created thread_read table.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()

