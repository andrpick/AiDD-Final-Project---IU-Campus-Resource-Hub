"""
Messaging service with thread management.
"""
import html
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
    
    # Sanitize content
    content = html.escape(content)
    
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
    """Get all messages in a thread for a user. Automatically marks the thread as read when opened."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Verify user has access to this thread
        cursor.execute("""
            SELECT 1 FROM messages
            WHERE thread_id = ?
            AND (sender_id = ? OR receiver_id = ?)
            AND deleted = 0
            LIMIT 1
        """, (thread_id, user_id, user_id))
        
        if not cursor.fetchone():
            return {'success': False, 'error': 'Thread not found or access denied'}
        
        # Get all messages in the thread
        cursor.execute("""
            SELECT * FROM messages
            WHERE thread_id = ?
            AND (sender_id = ? OR receiver_id = ?)
            AND deleted = 0
            ORDER BY timestamp ASC
        """, (thread_id, user_id, user_id))
        
        messages = [dict(row) for row in cursor.fetchall()]
        
        # Automatically mark thread as read when opened
        cursor.execute("""
            INSERT INTO thread_read (user_id, thread_id, is_read, updated_at)
            VALUES (?, ?, 1, CURRENT_TIMESTAMP)
            ON CONFLICT(user_id, thread_id) DO UPDATE SET
                is_read = 1,
                updated_at = CURRENT_TIMESTAMP
        """, (user_id, thread_id))
        conn.commit()
    
    return {'success': True, 'data': {'messages': messages}}

def list_threads(user_id):
    """List all message threads for a user, including resource information and thread read status."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Get latest message per thread, including resource_id and thread read status
        cursor.execute("""
            SELECT m1.thread_id,
                   CASE 
                       WHEN m1.sender_id = ? THEN m1.receiver_id
                       ELSE m1.sender_id
                   END as other_user_id,
                   m1.content as last_message,
                   m1.timestamp as last_message_time,
                   m1.resource_id,
                   COALESCE(tr.is_read, 0) as is_read
            FROM messages m1
            LEFT JOIN thread_read tr ON m1.thread_id = tr.thread_id AND tr.user_id = ?
            WHERE (m1.sender_id = ? OR m1.receiver_id = ?)
            AND m1.deleted = 0
            AND m1.timestamp = (
                SELECT MAX(timestamp)
                FROM messages
                WHERE thread_id = m1.thread_id
                AND deleted = 0
            )
            GROUP BY m1.thread_id, other_user_id, m1.content, m1.timestamp, m1.resource_id, tr.is_read
            ORDER BY last_message_time DESC
        """, (user_id, user_id, user_id, user_id))
        
        threads = []
        for row in cursor.fetchall():
            thread = dict(row)
            # Get other user info
            other_user_id = thread['other_user_id']
            cursor.execute("SELECT name, email FROM users WHERE user_id = ?", (other_user_id,))
            other_user = cursor.fetchone()
            if other_user:
                thread['other_user_name'] = other_user['name']
                thread['other_user_email'] = other_user['email']
            
            # Get resource info if resource_id exists
            if thread.get('resource_id'):
                cursor.execute("SELECT resource_id, title FROM resources WHERE resource_id = ?", (thread['resource_id'],))
                resource = cursor.fetchone()
                if resource:
                    thread['resource_title'] = resource['title']
                    thread['resource_id'] = resource['resource_id']
            
            # Thread is unread if is_read is 0 or NULL (defaults to unread)
            # COALESCE already handles NULL as 0, so we check if is_read == 0
            thread['is_unread'] = (thread.get('is_read', 0) == 0)
            
            threads.append(thread)
    
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
    
    return {'success': True, 'data': {'message_id': message_id}}

def search_users_for_messaging(current_user_id, search=None, limit=50):
    """Search for users that can be messaged (excluding suspended users and current user)."""
    conditions = ["suspended = 0", "user_id != ?"]
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

