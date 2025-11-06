"""
Messaging service with thread management.
"""
from src.data_access.database import get_db_connection

def generate_thread_id(user1_id, user2_id, resource_id=None):
    """Generate deterministic thread ID from two user IDs and optional resource_id.
    
    If resource_id is provided, each (user1, user2, resource) combination gets a unique thread.
    If resource_id is None, falls back to user-only threading (legacy support).
    """
    smaller_id = min(user1_id, user2_id)
    larger_id = max(user1_id, user2_id)
    
    if resource_id is not None:
        # Thread per resource: (user1, user2, resource_id)
        thread_id = hash(f"{smaller_id}_{larger_id}_{resource_id}")
    else:
        # Legacy: thread per user pair only
        thread_id = hash(f"{smaller_id}_{larger_id}")
    
    # Ensure positive integer
    return abs(thread_id) % (10 ** 10)

def send_message(sender_id, receiver_id, content, resource_id=None):
    """Send a message between two users, optionally about a specific resource.
    
    When a new message is sent, the thread is automatically marked as unread for the receiver
    (if it doesn't exist in thread_read, it defaults to unread).
    
    Args:
        sender_id: User ID of the sender
        receiver_id: User ID of the receiver
        content: Message content
        resource_id: Optional resource ID to group messages by resource
    """
    if sender_id == receiver_id:
        return {'success': False, 'error': 'Cannot send message to yourself'}
    
    if not content or len(content.strip()) == 0:
        return {'success': False, 'error': 'Message content cannot be empty'}
    
    if len(content) > 2000:
        return {'success': False, 'error': 'Message must be less than 2000 characters'}
    
    # Don't escape here - let Jinja2 templates handle escaping for security
    # This prevents double-escaping which causes HTML entities to display incorrectly
    thread_id = generate_thread_id(sender_id, receiver_id, resource_id)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages (thread_id, sender_id, receiver_id, content, resource_id)
            VALUES (?, ?, ?, ?, ?)
        """, (thread_id, sender_id, receiver_id, content, resource_id))
        
        message_id = cursor.lastrowid
        
        # When a new message is sent, mark the thread as unread for the receiver
        # This ensures new messages are always marked as unread
        cursor.execute("""
            INSERT INTO thread_read (user_id, thread_id, is_read, updated_at)
            VALUES (?, ?, 0, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, thread_id) DO UPDATE SET
                is_read = 0,
                updated_at = CURRENT_TIMESTAMP
        """, (receiver_id, thread_id))
        conn.commit()
    
    return {'success': True, 'data': {'message_id': message_id, 'thread_id': thread_id}}

def get_thread_messages(thread_id, user_id):
    """Get all messages in a thread for a user. Automatically marks the thread as read when opened.
    
    This function consolidates messages across all thread_ids for the same (other_user_id, resource_id)
    combination to ensure all messages are shown even if they have different legacy thread_ids.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # First, get one message to determine other_user_id and resource_id
        cursor.execute("""
            SELECT sender_id, receiver_id, resource_id
            FROM messages
            WHERE thread_id = ?
            AND (sender_id = ? OR receiver_id = ?)
            AND deleted = 0
            LIMIT 1
        """, (thread_id, user_id, user_id))
        
        first_message = cursor.fetchone()
        if not first_message:
            return {'success': False, 'error': 'Thread not found or access denied'}
        
        # Determine other_user_id and resource_id
        if first_message['sender_id'] == user_id:
            other_user_id = first_message['receiver_id']
        else:
            other_user_id = first_message['sender_id']
        resource_id = first_message['resource_id']
        
        # Get all messages for this (other_user_id, resource_id) combination across all thread_ids
        # This consolidates messages that may have different thread_ids due to legacy data
        cursor.execute("""
            SELECT * FROM messages
            WHERE (sender_id = ? OR receiver_id = ?)
            AND (sender_id = ? OR receiver_id = ?)
            AND (resource_id = ? OR (? IS NULL AND resource_id IS NULL))
            AND deleted = 0
            ORDER BY timestamp ASC
        """, (user_id, user_id, other_user_id, other_user_id, resource_id, resource_id))
        
        messages = [dict(row) for row in cursor.fetchall()]
        
        # Mark all thread_ids for this user-resource combination as read
        # Get all thread_ids for this combination
        cursor.execute("""
            SELECT DISTINCT thread_id
            FROM messages
            WHERE (sender_id = ? OR receiver_id = ?)
            AND (sender_id = ? OR receiver_id = ?)
            AND (resource_id = ? OR (? IS NULL AND resource_id IS NULL))
            AND deleted = 0
        """, (user_id, user_id, other_user_id, other_user_id, resource_id, resource_id))
        
        thread_ids = [row['thread_id'] for row in cursor.fetchall()]
        
        # Mark all thread_ids as read
        for tid in thread_ids:
            cursor.execute("""
                INSERT INTO thread_read (user_id, thread_id, is_read, updated_at)
                VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id, thread_id) DO UPDATE SET
                    is_read = 1,
                    updated_at = CURRENT_TIMESTAMP
            """, (user_id, tid))
        conn.commit()
    
    return {'success': True, 'data': {'messages': messages}}

def list_threads(user_id):
    """List all message threads for a user, including resource information and thread read status.
    
    Threads are consolidated by (other_user_id, resource_id) combination, so there's only
    one thread per user-resource pair, regardless of legacy thread_ids.
    """
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Get all messages for the user, grouped by (other_user_id, resource_id)
        # This consolidates threads that may have different thread_ids due to legacy data
        cursor.execute("""
            SELECT 
                   CASE 
                       WHEN m.sender_id = ? THEN m.receiver_id
                       ELSE m.sender_id
                   END as other_user_id,
                   m.resource_id,
                   MAX(m.timestamp) as last_message_time
            FROM messages m
            WHERE (m.sender_id = ? OR m.receiver_id = ?)
            AND m.deleted = 0
            GROUP BY 
                CASE 
                    WHEN m.sender_id = ? THEN m.receiver_id
                    ELSE m.sender_id
                END,
                m.resource_id
        """, (user_id, user_id, user_id, user_id))
        
        # Get the latest message for each (other_user_id, resource_id) combination
        consolidated_threads = {}
        for row in cursor.fetchall():
            other_user_id = row['other_user_id']
            resource_id = row['resource_id']
            last_message_time = row['last_message_time']
            
            # Get the actual latest message with full details
            cursor.execute("""
                SELECT m.thread_id,
                       m.content as last_message,
                       m.timestamp as last_message_time,
                       m.resource_id,
                       CASE 
                           WHEN m.sender_id = ? THEN m.receiver_id
                           ELSE m.sender_id
                       END as other_user_id
                FROM messages m
                WHERE (m.sender_id = ? OR m.receiver_id = ?)
                AND m.deleted = 0
                AND (
                    CASE 
                        WHEN m.sender_id = ? THEN m.receiver_id
                        ELSE m.sender_id
                    END = ?
                )
                AND (m.resource_id = ? OR (? IS NULL AND m.resource_id IS NULL))
                AND m.timestamp = ?
                ORDER BY m.timestamp DESC
                LIMIT 1
            """, (user_id, user_id, user_id, user_id, other_user_id, resource_id, resource_id, last_message_time))
            
            message_row = cursor.fetchone()
            if message_row:
                # Create a unique key for this user-resource combination
                thread_key = f"{other_user_id}_{resource_id if resource_id else 'NULL'}"
                
                # Get read status for all thread_ids matching this user-resource combination
                # A thread is unread if ANY of its thread_ids are unread
                cursor.execute("""
                    SELECT DISTINCT m.thread_id
                    FROM messages m
                    WHERE (m.sender_id = ? OR m.receiver_id = ?)
                    AND m.deleted = 0
                    AND (
                        CASE 
                            WHEN m.sender_id = ? THEN m.receiver_id
                            ELSE m.sender_id
                        END = ?
                    )
                    AND (m.resource_id = ? OR (? IS NULL AND m.resource_id IS NULL))
                """, (user_id, user_id, user_id, other_user_id, resource_id, resource_id))
                
                thread_ids = [row['thread_id'] for row in cursor.fetchall()]
                
                # Check if any thread_id is unread
                is_unread = False
                if thread_ids:
                    placeholders = ','.join(['?'] * len(thread_ids))
                    cursor.execute(f"""
                        SELECT COUNT(*) as unread_count
                        FROM thread_read tr
                        WHERE tr.thread_id IN ({placeholders})
                        AND tr.user_id = ?
                        AND tr.is_read = 0
                    """, thread_ids + [user_id])
                    
                    unread_result = cursor.fetchone()
                    if unread_result and unread_result['unread_count'] > 0:
                        is_unread = True
                    else:
                        # If no thread_read entries exist for any of these thread_ids, default to unread
                        cursor.execute(f"""
                            SELECT COUNT(*) as read_count
                            FROM thread_read tr
                            WHERE tr.thread_id IN ({placeholders})
                            AND tr.user_id = ?
                            AND tr.is_read = 1
                        """, thread_ids + [user_id])
                        
                        read_result = cursor.fetchone()
                        # If no read entries exist, thread is unread
                        if not read_result or read_result['read_count'] == 0:
                            is_unread = True
                
                consolidated_threads[thread_key] = {
                    'thread_id': message_row['thread_id'],  # Use the thread_id of the latest message
                    'other_user_id': other_user_id,
                    'resource_id': resource_id,
                    'last_message': message_row['last_message'],
                    'last_message_time': message_row['last_message_time'],
                    'is_unread': is_unread
                }
        
        # Convert to list and enrich with user/resource info
        threads = []
        for thread_key, thread in consolidated_threads.items():
            # Get other user info (handle deleted users)
            other_user_id = thread['other_user_id']
            cursor.execute("SELECT name, email, profile_image FROM users WHERE user_id = ? AND (deleted = 0 OR deleted IS NULL)", (other_user_id,))
            other_user = cursor.fetchone()
            if other_user:
                thread['other_user_name'] = other_user['name'] or '[Deleted User]'
                thread['other_user_email'] = other_user['email'] or '[Deleted]'
                thread['other_user_profile_image'] = other_user['profile_image']
            else:
                thread['other_user_name'] = '[Deleted User]'
                thread['other_user_email'] = '[Deleted]'
                thread['other_user_profile_image'] = None
            
            # Get resource info if resource_id exists
            if thread.get('resource_id'):
                cursor.execute("SELECT resource_id, title FROM resources WHERE resource_id = ?", (thread['resource_id'],))
                resource = cursor.fetchone()
                if resource:
                    thread['resource_title'] = resource['title']
                    thread['resource_id'] = resource['resource_id']
            
            threads.append(thread)
        
        # Sort by last_message_time descending
        threads.sort(key=lambda t: t['last_message_time'], reverse=True)
    
    return {'success': True, 'data': {'threads': threads}}

def delete_message(message_id, user_id):
    """Soft delete a message."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Verify user owns the message
        cursor.execute("SELECT sender_id, receiver_id FROM messages WHERE message_id = ?", (message_id,))
        message = cursor.fetchone()
        
        if not message:
            return {'success': False, 'error': 'Message not found'}
        
        if message['sender_id'] != user_id and message['receiver_id'] != user_id:
            return {'success': False, 'error': 'Unauthorized'}
        
        cursor.execute("UPDATE messages SET deleted = 1 WHERE message_id = ?", (message_id,))
        conn.commit()
    
    return {'success': True, 'data': {'message_id': message_id}}

def delete_thread(thread_id, user_id):
    """Soft delete all messages in a thread for a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # First, get one message to determine other_user_id and resource_id
        cursor.execute("""
            SELECT sender_id, receiver_id, resource_id
            FROM messages
            WHERE thread_id = ?
            AND (sender_id = ? OR receiver_id = ?)
            AND deleted = 0
            LIMIT 1
        """, (thread_id, user_id, user_id))
        
        first_message = cursor.fetchone()
        if not first_message:
            return {'success': False, 'error': 'Thread not found or access denied'}
        
        # Determine other_user_id and resource_id
        if first_message['sender_id'] == user_id:
            other_user_id = first_message['receiver_id']
        else:
            other_user_id = first_message['sender_id']
        resource_id = first_message['resource_id']
        
        # Soft delete all messages for this (other_user_id, resource_id) combination
        # This matches the thread consolidation logic in get_thread_messages
        cursor.execute("""
            UPDATE messages 
            SET deleted = 1 
            WHERE (sender_id = ? OR receiver_id = ?)
            AND (sender_id = ? OR receiver_id = ?)
            AND (resource_id = ? OR (? IS NULL AND resource_id IS NULL))
            AND deleted = 0
        """, (user_id, user_id, other_user_id, other_user_id, resource_id, resource_id))
        
        deleted_count = cursor.rowcount
        conn.commit()
    
    return {'success': True, 'data': {'thread_id': thread_id, 'deleted_count': deleted_count}}

def get_deleted_threads(admin_user_id, limit=100, offset=0):
    """Get all deleted threads for an admin user. Admin only."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verify user is admin
        cursor.execute("SELECT role FROM users WHERE user_id = ?", (admin_user_id,))
        user = cursor.fetchone()
        if not user or user['role'] != 'admin':
            return {'success': False, 'error': 'Admin access required'}
        
        # Find all unique (user1_id, user2_id, resource_id) combinations that have deleted messages
        # This represents deleted threads
        cursor.execute("""
            SELECT DISTINCT
                CASE 
                    WHEN m1.sender_id < m1.receiver_id THEN m1.sender_id
                    ELSE m1.receiver_id
                END as user1_id,
                CASE 
                    WHEN m1.sender_id < m1.receiver_id THEN m1.receiver_id
                    ELSE m1.sender_id
                END as user2_id,
                m1.resource_id,
                MAX(m1.timestamp) as last_message_time
            FROM messages m1
            WHERE m1.deleted = 1
            GROUP BY 
                CASE 
                    WHEN m1.sender_id < m1.receiver_id THEN m1.sender_id
                    ELSE m1.receiver_id
                END,
                CASE 
                    WHEN m1.sender_id < m1.receiver_id THEN m1.receiver_id
                    ELSE m1.sender_id
                END,
                m1.resource_id
            ORDER BY last_message_time DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        thread_keys = cursor.fetchall()
        threads = []
        
        for row in thread_keys:
            user1_id = row['user1_id']
            user2_id = row['user2_id']
            resource_id = row['resource_id']
            last_message_time = row['last_message_time']
            
            # Get one message to determine thread_id
            cursor.execute("""
                SELECT thread_id, content, sender_id, receiver_id
                FROM messages
                WHERE ((sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?))
                AND (resource_id = ? OR (? IS NULL AND resource_id IS NULL))
                AND deleted = 1
                ORDER BY timestamp DESC
                LIMIT 1
            """, (user1_id, user2_id, user2_id, user1_id, resource_id, resource_id))
            
            message = cursor.fetchone()
            if not message:
                continue
            
            thread_id = message['thread_id']
            last_message = message['content']
            
            # Get user names
            cursor.execute("SELECT name, email FROM users WHERE user_id = ?", (user1_id,))
            user1 = cursor.fetchone()
            cursor.execute("SELECT name, email FROM users WHERE user_id = ?", (user2_id,))
            user2 = cursor.fetchone()
            
            user1_name = user1['name'] if user1 else '[Deleted User]'
            user2_name = user2['name'] if user2 else '[Deleted User]'
            
            # Get resource title if applicable
            resource_title = None
            if resource_id:
                cursor.execute("SELECT title FROM resources WHERE resource_id = ?", (resource_id,))
                resource = cursor.fetchone()
                if resource:
                    resource_title = resource['title']
            
            # Count deleted messages in this thread
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM messages
                WHERE ((sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?))
                AND (resource_id = ? OR (? IS NULL AND resource_id IS NULL))
                AND deleted = 1
            """, (user1_id, user2_id, user2_id, user1_id, resource_id, resource_id))
            
            deleted_count = cursor.fetchone()['count']
            
            threads.append({
                'thread_id': thread_id,
                'user1_id': user1_id,
                'user2_id': user2_id,
                'user1_name': user1_name,
                'user2_name': user2_name,
                'resource_id': resource_id,
                'resource_title': resource_title,
                'last_message': last_message,
                'last_message_time': last_message_time,
                'deleted_count': deleted_count
            })
        
        # Get total count
        cursor.execute("""
            SELECT COUNT(DISTINCT 
                CASE 
                    WHEN sender_id < receiver_id THEN sender_id || '-' || receiver_id || '-' || COALESCE(CAST(resource_id AS TEXT), 'NULL')
                    ELSE receiver_id || '-' || sender_id || '-' || COALESCE(CAST(resource_id AS TEXT), 'NULL')
                END
            ) as count
            FROM messages
            WHERE deleted = 1
        """)
        total = cursor.fetchone()['count']
    
    return {'success': True, 'data': {'threads': threads, 'total': total}}

def restore_thread(thread_id, user_id):
    """Restore all messages in a soft-deleted thread for a user. Admin only."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verify user is admin
        cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user or user['role'] != 'admin':
            return {'success': False, 'error': 'Admin access required'}
        
        # First, get one message to determine other_user_id and resource_id
        cursor.execute("""
            SELECT sender_id, receiver_id, resource_id
            FROM messages
            WHERE thread_id = ?
            AND (sender_id = ? OR receiver_id = ?)
            LIMIT 1
        """, (thread_id, user_id, user_id))
        
        first_message = cursor.fetchone()
        if not first_message:
            return {'success': False, 'error': 'Thread not found or access denied'}
        
        # Determine other_user_id and resource_id
        if first_message['sender_id'] == user_id:
            other_user_id = first_message['receiver_id']
        else:
            other_user_id = first_message['sender_id']
        resource_id = first_message['resource_id']
        
        # Check if there are any deleted messages to restore
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM messages
            WHERE (sender_id = ? OR receiver_id = ?)
            AND (sender_id = ? OR receiver_id = ?)
            AND (resource_id = ? OR (? IS NULL AND resource_id IS NULL))
            AND deleted = 1
        """, (user_id, user_id, other_user_id, other_user_id, resource_id, resource_id))
        
        result = cursor.fetchone()
        if not result or result['count'] == 0:
            return {'success': False, 'error': 'No deleted messages found in this thread'}
        
        # Restore all messages for this thread
        cursor.execute("""
            UPDATE messages 
            SET deleted = 0 
            WHERE (sender_id = ? OR receiver_id = ?)
            AND (sender_id = ? OR receiver_id = ?)
            AND (resource_id = ? OR (? IS NULL AND resource_id IS NULL))
            AND deleted = 1
        """, (user_id, user_id, other_user_id, other_user_id, resource_id, resource_id))
        
        restored_count = cursor.rowcount
        conn.commit()
    
    return {'success': True, 'data': {'thread_id': thread_id, 'restored_count': restored_count}}

def restore_message(message_id, user_id):
    """Restore a soft-deleted message."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verify user owns the message
        cursor.execute("SELECT sender_id, receiver_id, deleted FROM messages WHERE message_id = ?", (message_id,))
        message = cursor.fetchone()
        
        if not message:
            return {'success': False, 'error': 'Message not found'}
        
        if message['sender_id'] != user_id and message['receiver_id'] != user_id:
            return {'success': False, 'error': 'Unauthorized'}
        
        if not message['deleted']:
            return {'success': False, 'error': 'Message is not deleted'}
        
        cursor.execute("UPDATE messages SET deleted = 0 WHERE message_id = ?", (message_id,))
        conn.commit()
    
    return {'success': True, 'data': {'message_id': message_id}}

def search_users_for_messaging(current_user_id, search=None, limit=50):
    """Search for users that can be messaged (excluding suspended and deleted users, and current user)."""
    conditions = ["(suspended = 0 OR suspended IS NULL)", "(deleted = 0 OR deleted IS NULL)", "user_id != ?"]
    values = [current_user_id]
    
    if search:
        conditions.append("(name LIKE ? OR email LIKE ?)")
        search_pattern = f"%{search}%"
        values.extend([search_pattern, search_pattern])
    
    where_clause = " AND ".join(conditions)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT user_id, name, email, role, department
            FROM users
            WHERE {where_clause}
            ORDER BY name ASC
            LIMIT ?
        """, values + [limit])
        
        users = [dict(row) for row in cursor.fetchall()]
    
    return {'success': True, 'data': {'users': users}}

def get_existing_thread_id(user1_id, user2_id, resource_id=None):
    """Get existing thread ID between two users for a specific resource, if it exists.
    
    Args:
        user1_id: First user ID
        user2_id: Second user ID
        resource_id: Optional resource ID to find resource-specific thread
    
    Returns:
        Thread ID if exists, None otherwise
    """
    thread_id = generate_thread_id(user1_id, user2_id, resource_id)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT thread_id 
            FROM messages
            WHERE thread_id = ?
            AND (sender_id = ? OR receiver_id = ?)
            AND (sender_id = ? OR receiver_id = ?)
            AND (resource_id = ? OR (? IS NULL AND resource_id IS NULL))
            AND deleted = 0
            LIMIT 1
        """, (thread_id, user1_id, user1_id, user2_id, user2_id, resource_id, resource_id))
        
        result = cursor.fetchone()
        if result:
            return result['thread_id']
    
    return None

def get_unread_count(user_id):
    """Get total count of unread threads for a user (thread-level read status)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Count threads that are not marked as read (or don't exist in thread_read table)
        # A thread is unread if:
        # 1. No entry exists in thread_read (defaults to unread)
        # 2. Entry exists with is_read = 0
        cursor.execute("""
            SELECT COUNT(DISTINCT m.thread_id)
            FROM messages m
            LEFT JOIN thread_read tr ON m.thread_id = tr.thread_id AND tr.user_id = ?
            WHERE (m.sender_id = ? OR m.receiver_id = ?)
            AND (tr.is_read = 0 OR tr.is_read IS NULL)
            AND m.deleted = 0
        """, (user_id, user_id, user_id))
        
        count = cursor.fetchone()[0]
    
    return count

def mark_message_read(message_id, user_id):
    """Mark a specific message as read. User must be the receiver."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Verify user is the receiver
        cursor.execute("SELECT receiver_id FROM messages WHERE message_id = ?", (message_id,))
        message = cursor.fetchone()
        
        if not message:
            return {'success': False, 'error': 'Message not found'}
        
        if message['receiver_id'] != user_id:
            return {'success': False, 'error': 'Unauthorized'}
        
        cursor.execute("UPDATE messages SET read = 1 WHERE message_id = ?", (message_id,))
        conn.commit()
    
    return {'success': True, 'data': {'message_id': message_id}}

def mark_message_unread(message_id, user_id):
    """Mark a specific message as unread. User must be the receiver."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Verify user is the receiver
        cursor.execute("SELECT receiver_id FROM messages WHERE message_id = ?", (message_id,))
        message = cursor.fetchone()
        
        if not message:
            return {'success': False, 'error': 'Message not found'}
        
        if message['receiver_id'] != user_id:
            return {'success': False, 'error': 'Unauthorized'}
        
        cursor.execute("UPDATE messages SET read = 0 WHERE message_id = ?", (message_id,))
        conn.commit()
    
    return {'success': True, 'data': {'message_id': message_id}}

def mark_thread_read(thread_id, user_id):
    """Mark a thread as read for the user (thread-level status)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Check if thread exists and user has access
        cursor.execute("""
            SELECT 1 FROM messages
            WHERE thread_id = ?
            AND (sender_id = ? OR receiver_id = ?)
            AND deleted = 0
            LIMIT 1
        """, (thread_id, user_id, user_id))
        
        if not cursor.fetchone():
            return {'success': False, 'error': 'Thread not found or access denied'}
        
        # Insert or update thread_read status
        cursor.execute("""
            INSERT INTO thread_read (user_id, thread_id, is_read, updated_at)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, thread_id) DO UPDATE SET
                is_read = 1,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, thread_id))
        conn.commit()
    
    return {'success': True, 'data': {'thread_id': thread_id}}

def mark_thread_unread(thread_id, user_id):
    """Mark a thread as unread for the user (thread-level status)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Check if thread exists and user has access
        cursor.execute("""
            SELECT 1 FROM messages
            WHERE thread_id = ?
            AND (sender_id = ? OR receiver_id = ?)
            AND deleted = 0
            LIMIT 1
        """, (thread_id, user_id, user_id))
        
        if not cursor.fetchone():
            return {'success': False, 'error': 'Thread not found or access denied'}
        
        # Insert or update thread_read status
        cursor.execute("""
            INSERT INTO thread_read (user_id, thread_id, is_read, updated_at)
            VALUES (?, ?, 0, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, thread_id) DO UPDATE SET
                is_read = 0,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, thread_id))
        conn.commit()
    
    return {'success': True, 'data': {'thread_id': thread_id}}

