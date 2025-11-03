#!/usr/bin/env python3
"""
Cleanup script to remove test-generated users and resources from the database.

This script removes all data except:
- Users with IDs: 1, 2, 3, 4
- Resources with IDs: 1, 2, 3, 4, 5, 6, 7, 8, 9

All other users, resources, and related data will be deleted.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.data_access.database import get_db_connection

def cleanup_test_data():
    """Remove all users and resources except specified IDs."""
    
    # Define preserved IDs
    PRESERVED_USER_IDS = [1, 2, 3, 4]
    PRESERVED_RESOURCE_IDS = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    
    print("Starting cleanup of test-generated data...")
    print("-" * 80)
    print(f"Preserving users with IDs: {PRESERVED_USER_IDS}")
    print(f"Preserving resources with IDs: {PRESERVED_RESOURCE_IDS}")
    print("-" * 80)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Show current state
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM resources")
        total_resources = cursor.fetchone()[0]
        print(f"\nCurrent state:")
        print(f"  - Total users: {total_users}")
        print(f"  - Total resources: {total_resources}")
        
        # Show preserved users
        print(f"\n1. Checking preserved users...")
        placeholders = ','.join(['?' for _ in PRESERVED_USER_IDS])
        cursor.execute(f"""
            SELECT user_id, email, name, role
            FROM users
            WHERE user_id IN ({placeholders})
        """, PRESERVED_USER_IDS)
        preserved_users = cursor.fetchall()
        print(f"   Found {len(preserved_users)} preserved users:")
        for user in preserved_users:
            print(f"   - ID {user['user_id']}: {user['email']} ({user['name']}, {user['role']})")
        
        # Show preserved resources
        print(f"\n2. Checking preserved resources...")
        placeholders = ','.join(['?' for _ in PRESERVED_RESOURCE_IDS])
        cursor.execute(f"""
            SELECT resource_id, title, owner_id
            FROM resources
            WHERE resource_id IN ({placeholders})
        """, PRESERVED_RESOURCE_IDS)
        preserved_resources = cursor.fetchall()
        print(f"   Found {len(preserved_resources)} preserved resources:")
        for resource in preserved_resources:
            print(f"   - ID {resource['resource_id']}: {resource['title']} (Owner: {resource['owner_id']})")
        
        # Delete bookings for resources that will be deleted
        print(f"\n3. Cleaning up bookings for resources to be deleted...")
        placeholders = ','.join(['?' for _ in PRESERVED_RESOURCE_IDS])
        cursor.execute(f"""
            DELETE FROM bookings
            WHERE resource_id NOT IN ({placeholders})
        """, PRESERVED_RESOURCE_IDS)
        bookings_deleted = cursor.rowcount
        print(f"   Deleted {bookings_deleted} bookings")
        
        # Delete bookings for users that will be deleted
        print(f"\n4. Cleaning up bookings for users to be deleted...")
        placeholders = ','.join(['?' for _ in PRESERVED_USER_IDS])
        cursor.execute(f"""
            DELETE FROM bookings
            WHERE requester_id NOT IN ({placeholders})
        """, PRESERVED_USER_IDS)
        bookings_deleted2 = cursor.rowcount
        print(f"   Deleted {bookings_deleted2} additional bookings")
        
        # Delete reviews for resources that will be deleted
        print(f"\n5. Cleaning up reviews for resources to be deleted...")
        placeholders = ','.join(['?' for _ in PRESERVED_RESOURCE_IDS])
        cursor.execute(f"""
            DELETE FROM reviews
            WHERE resource_id NOT IN ({placeholders})
        """, PRESERVED_RESOURCE_IDS)
        reviews_deleted = cursor.rowcount
        print(f"   Deleted {reviews_deleted} reviews")
        
        # Delete reviews for users that will be deleted
        print(f"\n6. Cleaning up reviews for users to be deleted...")
        placeholders = ','.join(['?' for _ in PRESERVED_USER_IDS])
        cursor.execute(f"""
            DELETE FROM reviews
            WHERE reviewer_id NOT IN ({placeholders})
        """, PRESERVED_USER_IDS)
        reviews_deleted2 = cursor.rowcount
        print(f"   Deleted {reviews_deleted2} additional reviews")
        
        # Delete messages for users that will be deleted
        print(f"\n7. Cleaning up messages for users to be deleted...")
        placeholders = ','.join(['?' for _ in PRESERVED_USER_IDS])
        cursor.execute(f"""
            DELETE FROM messages
            WHERE sender_id NOT IN ({placeholders})
            OR receiver_id NOT IN ({placeholders})
        """, PRESERVED_USER_IDS + PRESERVED_USER_IDS)
        messages_deleted = cursor.rowcount
        print(f"   Deleted {messages_deleted} messages")
        
        # Delete messages for resources that will be deleted
        print(f"\n8. Cleaning up messages for resources to be deleted...")
        placeholders = ','.join(['?' for _ in PRESERVED_RESOURCE_IDS])
        cursor.execute(f"""
            DELETE FROM messages
            WHERE resource_id IS NOT NULL
            AND resource_id NOT IN ({placeholders})
        """, PRESERVED_RESOURCE_IDS)
        messages_deleted2 = cursor.rowcount
        print(f"   Deleted {messages_deleted2} additional messages")
        
        # Delete thread_read for users that will be deleted
        print(f"\n9. Cleaning up thread_read for users to be deleted...")
        placeholders = ','.join(['?' for _ in PRESERVED_USER_IDS])
        cursor.execute(f"""
            DELETE FROM thread_read
            WHERE user_id NOT IN ({placeholders})
        """, PRESERVED_USER_IDS)
        thread_read_deleted = cursor.rowcount
        print(f"   Deleted {thread_read_deleted} thread_read records")
        
        # Delete admin_logs for users that will be deleted
        print(f"\n10. Cleaning up admin_logs for users to be deleted...")
        placeholders = ','.join(['?' for _ in PRESERVED_USER_IDS])
        cursor.execute(f"""
            DELETE FROM admin_logs
            WHERE admin_id NOT IN ({placeholders})
        """, PRESERVED_USER_IDS)
        admin_logs_deleted = cursor.rowcount
        print(f"   Deleted {admin_logs_deleted} admin log entries")
        
        # Delete resources that are not preserved
        print(f"\n11. Deleting resources (keeping IDs {PRESERVED_RESOURCE_IDS})...")
        placeholders = ','.join(['?' for _ in PRESERVED_RESOURCE_IDS])
        cursor.execute(f"""
            DELETE FROM resources
            WHERE resource_id NOT IN ({placeholders})
        """, PRESERVED_RESOURCE_IDS)
        resources_deleted = cursor.rowcount
        print(f"   Deleted {resources_deleted} resources")
        
        # Delete users that are not preserved
        print(f"\n12. Deleting users (keeping IDs {PRESERVED_USER_IDS})...")
        placeholders = ','.join(['?' for _ in PRESERVED_USER_IDS])
        cursor.execute(f"""
            DELETE FROM users
            WHERE user_id NOT IN ({placeholders})
        """, PRESERVED_USER_IDS)
        users_deleted = cursor.rowcount
        print(f"   Deleted {users_deleted} users")
        
        # Commit all changes
        conn.commit()
        
        print("\n" + "-" * 80)
        print("[SUCCESS] Cleanup completed!")
        print("\nFinal state:")
        
        # Show remaining users
        cursor.execute("SELECT user_id, email, name, role FROM users ORDER BY user_id")
        remaining_users = cursor.fetchall()
        print(f"  - Users ({len(remaining_users)}):")
        for user in remaining_users:
            print(f"    ID {user['user_id']}: {user['email']} ({user['name']}, {user['role']})")
        
        # Show remaining resources
        cursor.execute("SELECT resource_id, title, owner_id FROM resources ORDER BY resource_id")
        remaining_resources = cursor.fetchall()
        print(f"  - Resources ({len(remaining_resources)}):")
        for resource in remaining_resources:
            print(f"    ID {resource['resource_id']}: {resource['title']} (Owner: {resource['owner_id']})")
        
        # Show remaining bookings
        cursor.execute("SELECT COUNT(*) FROM bookings")
        booking_count = cursor.fetchone()[0]
        print(f"  - Bookings: {booking_count}")
        
        # Show remaining reviews
        cursor.execute("SELECT COUNT(*) FROM reviews")
        review_count = cursor.fetchone()[0]
        print(f"  - Reviews: {review_count}")
        
        # Show remaining messages
        cursor.execute("SELECT COUNT(*) FROM messages")
        message_count = cursor.fetchone()[0]
        print(f"  - Messages: {message_count}")

if __name__ == '__main__':
    try:
        cleanup_test_data()
    except Exception as e:
        print(f"\n[ERROR] Cleanup failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

