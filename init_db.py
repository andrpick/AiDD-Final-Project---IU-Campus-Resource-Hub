"""
Database initialization script for Indiana University Campus Resource Hub.
Creates all tables, indexes, and default admin user.
"""
import sqlite3
import bcrypt
import os
from pathlib import Path

def init_database():
    """Initialize database with schema and default data."""
    # Read database path dynamically from environment
    db_path = os.environ.get('DATABASE_PATH', 'campus_resource_hub.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('student', 'staff', 'admin')),
            department TEXT,
            profile_image TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            suspended BOOLEAN DEFAULT 0,
            suspended_reason TEXT,
            suspended_at DATETIME
        )
    """)
    
    # Create resources table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resources (
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
    
    # Create bookings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id INTEGER NOT NULL,
            requester_id INTEGER NOT NULL,
            start_datetime DATETIME NOT NULL,
            end_datetime DATETIME NOT NULL,
            status TEXT DEFAULT 'approved' CHECK(status IN ('approved', 'cancelled', 'completed')),
            rejection_reason TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (resource_id) REFERENCES resources(resource_id),
            FOREIGN KEY (requester_id) REFERENCES users(user_id)
        )
    """)
    
    # Create messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            message_id INTEGER PRIMARY KEY AUTOINCREMENT,
            thread_id INTEGER NOT NULL,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            resource_id INTEGER,
            content TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            read BOOLEAN DEFAULT 0,
            deleted BOOLEAN DEFAULT 0,
            FOREIGN KEY (sender_id) REFERENCES users(user_id),
            FOREIGN KEY (receiver_id) REFERENCES users(user_id),
            FOREIGN KEY (resource_id) REFERENCES resources(resource_id)
        )
    """)
    
    # Create thread_read table for tracking thread-level read/unread status
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS thread_read (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            thread_id INTEGER NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            UNIQUE(user_id, thread_id)
        )
    """)
    
    # Create reviews table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
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
            FOREIGN KEY (booking_id) REFERENCES bookings(booking_id),
            UNIQUE(resource_id, reviewer_id)
        )
    """)
    
    # Create admin_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS admin_logs (
            log_id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            target_table TEXT,
            target_id INTEGER,
            details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (admin_id) REFERENCES users(user_id)
        )
    """)
    
    # Create indexes
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)",
        "CREATE INDEX IF NOT EXISTS idx_resources_owner ON resources(owner_id)",
        "CREATE INDEX IF NOT EXISTS idx_resources_status ON resources(status)",
        "CREATE INDEX IF NOT EXISTS idx_resources_category ON resources(category)",
        "CREATE INDEX IF NOT EXISTS idx_bookings_resource ON bookings(resource_id)",
        "CREATE INDEX IF NOT EXISTS idx_bookings_requester ON bookings(requester_id)",
        "CREATE INDEX IF NOT EXISTS idx_bookings_datetime ON bookings(start_datetime, end_datetime)",
        "CREATE INDEX IF NOT EXISTS idx_messages_thread ON messages(thread_id)",
        "CREATE INDEX IF NOT EXISTS idx_reviews_resource ON reviews(resource_id)",
        "CREATE INDEX IF NOT EXISTS idx_reviews_reviewer ON reviews(reviewer_id)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    # Create default admin user if it doesn't exist
    admin_email = 'admin@example.com'
    admin_password = 'Admin123!'
    password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
    
    cursor.execute("SELECT user_id FROM users WHERE email = ?", (admin_email,))
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO users (name, email, password_hash, role)
            VALUES (?, ?, ?, ?)
        """, ('Admin User', admin_email, password_hash, 'admin'))
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized successfully at {db_path}")
    print(f"Default admin account created:")
    print(f"  Email: {admin_email}")
    print(f"  Password: {admin_password}")

if __name__ == '__main__':
    init_database()

