"""
Migration script to add resource_id column to messages table.
This allows messages to be grouped by resource, creating separate threads
for different resources even between the same users.
"""
import sqlite3
import os

# Database path
DB_PATH = os.environ.get('DATABASE_PATH', 'campus_resource_hub.db')

def migrate():
    """Add resource_id column to messages table."""
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Skipping migration.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(messages)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'resource_id' in columns:
            print("Column resource_id already exists in messages table. Skipping migration.")
            return
        
        # Add resource_id column (nullable initially for existing data)
        print("Adding resource_id column to messages table...")
        cursor.execute("""
            ALTER TABLE messages
            ADD COLUMN resource_id INTEGER
        """)
        
        # Add foreign key constraint if possible (SQLite limitations)
        # Note: SQLite doesn't support adding foreign keys via ALTER TABLE
        # We'll rely on application-level validation
        
        conn.commit()
        print("Successfully added resource_id column to messages table.")
        
        # Update existing messages to have NULL resource_id (general conversations)
        # This preserves existing data
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()

