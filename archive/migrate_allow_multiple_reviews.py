"""
Migration script to remove unique constraint on reviews table.
This allows users to review a resource multiple times.
"""
import sqlite3
import os

# Database path
DB_PATH = os.environ.get('DATABASE_PATH', 'campus_resource_hub.db')

def migrate():
    """Remove unique constraint from reviews table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Get existing reviews data
        cursor.execute("SELECT * FROM reviews")
        reviews_data = cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        reviews = [dict(zip(columns, row)) for row in reviews_data]
        
        # Drop the old table
        cursor.execute("DROP TABLE IF EXISTS reviews_old")
        cursor.execute("ALTER TABLE reviews RENAME TO reviews_old")
        
        # Create new table without unique constraint
        cursor.execute("""
            CREATE TABLE reviews (
                review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                resource_id INTEGER NOT NULL,
                reviewer_id INTEGER NOT NULL,
                booking_id INTEGER,
                rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
                comment TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (resource_id) REFERENCES resources(resource_id),
                FOREIGN KEY (reviewer_id) REFERENCES users(user_id),
                FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
            )
        """)
        
        # Reinsert data
        for review in reviews:
            cursor.execute("""
                INSERT INTO reviews (review_id, resource_id, reviewer_id, booking_id, rating, comment, timestamp, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                review['review_id'],
                review['resource_id'],
                review['reviewer_id'],
                review.get('booking_id'),
                review['rating'],
                review.get('comment'),
                review['timestamp'],
                review.get('updated_at', review['timestamp'])
            ))
        
        # Drop old table
        cursor.execute("DROP TABLE reviews_old")
        
        # Recreate index
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_resource ON reviews(resource_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_reviews_reviewer ON reviews(reviewer_id)")
        
        conn.commit()
        print("Migration completed successfully: Unique constraint removed from reviews table")
    except Exception as e:
        conn.rollback()
        print(f"Migration failed: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()

