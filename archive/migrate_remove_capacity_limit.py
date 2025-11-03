"""
Migration script to remove capacity limit of 500 from existing database.
This script recreates the resources table without the capacity <= 500 constraint.
"""
import sqlite3
import os
from pathlib import Path

# Database path
DB_PATH = os.environ.get('DATABASE_PATH', 'campus_resource_hub.db')

def migrate_remove_capacity_limit():
    """Remove capacity limit constraint from resources table."""
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Nothing to migrate.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        # Check if resources table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='resources'
        """)
        if not cursor.fetchone():
            print("Resources table does not exist. Nothing to migrate.")
            return
        
        # Get all data from existing table
        cursor.execute("SELECT * FROM resources")
        resources = cursor.fetchall()
        
        print(f"Found {len(resources)} resources to migrate.")
        
        # Create new table without the capacity limit
        cursor.execute("""
            CREATE TABLE resources_new (
                resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
                owner_id INTEGER NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT NOT NULL CHECK(category IN ('study_room', 'lab_equipment', 'av_equipment', 'event_space', 'tutoring', 'other')),
                location TEXT NOT NULL,
                capacity INTEGER NOT NULL CHECK(capacity > 0),
                images TEXT,
                availability_rules TEXT,
                status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'published', 'archived')),
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (owner_id) REFERENCES users(user_id)
            )
        """)
        
        # Copy all data from old table to new table
        for resource in resources:
            cursor.execute("""
                INSERT INTO resources_new 
                (resource_id, owner_id, title, description, category, location, capacity, 
                 images, availability_rules, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                resource['resource_id'],
                resource['owner_id'],
                resource['title'],
                resource['description'],
                resource['category'],
                resource['location'],
                resource['capacity'],
                resource['images'],
                resource['availability_rules'],
                resource['status'],
                resource['created_at'],
                resource['updated_at']
            ))
        
        # Drop old table
        cursor.execute("DROP TABLE resources")
        
        # Rename new table to original name
        cursor.execute("ALTER TABLE resources_new RENAME TO resources")
        
        # Recreate indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resources_owner ON resources(owner_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resources_status ON resources(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resources_category ON resources(category)")
        
        conn.commit()
        print(f"Migration completed successfully! {len(resources)} resources migrated.")
        print("Capacity limit of 500 has been removed from the resources table.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during migration: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate_remove_capacity_limit()

