"""
Migration script to make capacity optional (nullable) in resources table.
"""
import sqlite3
import os

DB_PATH = 'campus_resource_hub.db'

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found. Skipping migration.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Check current schema
        cursor.execute("PRAGMA table_info(resources)")
        columns = cursor.fetchall()
        capacity_col = next((col for col in columns if col[1] == 'capacity'), None)
        
        if capacity_col:
            # Check if capacity is already nullable
            if capacity_col[3] == 0:  # not null flag is 0 when nullable
                print("Capacity is already nullable. No migration needed.")
                return
            
            print("Making capacity nullable...")
            
            # Create new table with nullable capacity
            cursor.execute("""
                CREATE TABLE resources_new (
                    resource_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    category TEXT NOT NULL CHECK(category IN ('study_room', 'lab_equipment', 'av_equipment', 'event_space', 'tutoring', 'other')),
                    location TEXT NOT NULL,
                    capacity INTEGER CHECK(capacity IS NULL OR capacity > 0),
                    images TEXT,
                    availability_rules TEXT,
                    status TEXT DEFAULT 'draft' CHECK(status IN ('draft', 'published', 'archived')),
                    featured BOOLEAN DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (owner_id) REFERENCES users(user_id)
                )
            """)
            
            # Copy data from old table
            cursor.execute("""
                INSERT INTO resources_new 
                SELECT resource_id, owner_id, title, description, category, location, 
                       capacity, images, availability_rules, status, featured, 
                       created_at, updated_at
                FROM resources
            """)
            
            # Drop old table
            cursor.execute("DROP TABLE resources")
            
            # Rename new table
            cursor.execute("ALTER TABLE resources_new RENAME TO resources")
            
            conn.commit()
            print("Migration completed successfully. Capacity is now optional.")
            
        else:
            print("Capacity column not found. Skipping migration.")
            
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()

