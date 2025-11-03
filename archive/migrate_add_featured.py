"""
Migration script to add featured column to resources table.
"""
import sqlite3
import os

# Database path
DB_PATH = os.environ.get('DATABASE_PATH', 'campus_resource_hub.db')

def migrate_add_featured():
    """Add featured column to resources table."""
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Nothing to migrate.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if featured column already exists
        cursor.execute("PRAGMA table_info(resources)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'featured' in columns:
            print("Featured column already exists. Nothing to migrate.")
            return
        
        # Add featured column
        cursor.execute("""
            ALTER TABLE resources 
            ADD COLUMN featured BOOLEAN DEFAULT 0
        """)
        
        conn.commit()
        print("Migration completed successfully! Featured column added to resources table.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_add_featured()

