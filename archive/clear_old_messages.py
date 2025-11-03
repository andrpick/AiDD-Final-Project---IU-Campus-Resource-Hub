"""
Script to clear message history from before resource-based threading was implemented.
This will delete all messages where resource_id IS NULL (old messages).

Usage:
    python clear_old_messages.py          # Interactive mode (asks for confirmation)
    python clear_old_messages.py --yes    # Non-interactive mode (skips confirmation)
"""
import sqlite3
import os
import sys

# Database path
DB_PATH = os.environ.get('DATABASE_PATH', 'campus_resource_hub.db')

def clear_old_messages(skip_confirmation=False):
    """Delete all messages where resource_id IS NULL (old messages from before resource-based threading).
    
    Args:
        skip_confirmation: If True, skip the confirmation prompt
    """
    if not os.path.exists(DB_PATH):
        print(f"Database {DB_PATH} not found.")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Count messages to be deleted
        cursor.execute("SELECT COUNT(*) FROM messages WHERE resource_id IS NULL")
        count = cursor.fetchone()[0]
        
        if count == 0:
            print("No old messages found (all messages already have resource_id or table is empty).")
            return
        
        print(f"Found {count} old message(s) without resource_id.")
        
        if not skip_confirmation:
            response = input(f"Are you sure you want to delete {count} message(s)? (yes/no): ")
            if response.lower() != 'yes':
                print("Deletion cancelled.")
                return
        else:
            print(f"Deleting {count} message(s)...")
        
        # Delete messages where resource_id IS NULL
        cursor.execute("DELETE FROM messages WHERE resource_id IS NULL")
        deleted_count = cursor.rowcount
        
        conn.commit()
        print(f"Successfully deleted {deleted_count} old message(s).")
        
    except Exception as e:
        conn.rollback()
        print(f"Error during deletion: {e}")
        raise
    finally:
        conn.close()

if __name__ == '__main__':
    skip_confirmation = '--yes' in sys.argv or '-y' in sys.argv
    clear_old_messages(skip_confirmation=skip_confirmation)

