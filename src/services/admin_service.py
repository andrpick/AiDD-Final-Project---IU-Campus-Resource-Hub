"""
Admin service for user management and statistics.
"""
from src.data_access.database import get_db_connection

def get_statistics():
    """Get system statistics for admin dashboard."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # User statistics
        cursor.execute("""
            SELECT role, COUNT(*) as count
            FROM users
            WHERE suspended = 0
            GROUP BY role
        """)
        users_by_role = {row['role']: row['count'] for row in cursor.fetchall()}
        
        # Resource statistics
        cursor.execute("""
            SELECT category, status, COUNT(*) as count
            FROM resources
            GROUP BY category, status
        """)
        resources_by_category_status = {}
        for row in cursor.fetchall():
            key = f"{row['category']}_{row['status']}"
            resources_by_category_status[key] = row['count']
        
        # Resources by status
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM resources
            GROUP BY status
        """)
        resources_by_status = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Booking statistics
        cursor.execute("""
            SELECT status, COUNT(*) as count
            FROM bookings
            GROUP BY status
        """)
        bookings_by_status = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # Total bookings (all statuses)
        cursor.execute("SELECT COUNT(*) as count FROM bookings")
        total_bookings = cursor.fetchone()['count']
        
        # Review count
        cursor.execute("SELECT COUNT(*) as count FROM reviews")
        total_reviews = cursor.fetchone()['count']
        
        # Active users in last 30 days (users with bookings or reviews)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) as count
            FROM (
                SELECT requester_id as user_id FROM bookings
                WHERE created_at >= datetime('now', '-30 days')
                UNION
                SELECT reviewer_id as user_id FROM reviews
                WHERE timestamp >= datetime('now', '-30 days')
            )
        """)
        active_users = cursor.fetchone()['count']
        
        # Popular resources (most booked)
        cursor.execute("""
            SELECT r.resource_id, r.title, COUNT(b.booking_id) as booking_count
            FROM resources r
            LEFT JOIN bookings b ON r.resource_id = b.resource_id
            WHERE r.status = 'published'
            GROUP BY r.resource_id, r.title
            ORDER BY booking_count DESC
            LIMIT 10
        """)
        popular_resources = [dict(row) for row in cursor.fetchall()]
    
    return {
        'success': True,
        'data': {
            'users_by_role': users_by_role,
            'resources_by_category_status': resources_by_category_status,
            'resources_by_status': resources_by_status,
            'bookings_by_status': bookings_by_status,
            'total_bookings': total_bookings,
            'total_reviews': total_reviews,
            'active_users_30_days': active_users,
            'popular_resources': popular_resources
        }
    }

def list_users(role=None, suspended=None, department=None, search=None, limit=20, offset=0):
    """List users with filters."""
    conditions = []
    values = []
    
    if role:
        conditions.append("role = ?")
        values.append(role)
    
    if suspended is not None:
        conditions.append("suspended = ?")
        values.append(1 if suspended else 0)
    
    if department:
        conditions.append("department LIKE ?")
        values.append(f"%{department}%")
    
    if search:
        conditions.append("(name LIKE ? OR email LIKE ?)")
        search_pattern = f"%{search}%"
        values.extend([search_pattern, search_pattern])
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT user_id, name, email, role, department, suspended, created_at
            FROM users
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, values + [limit, offset])
        
        users = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute(f"SELECT COUNT(*) FROM users WHERE {where_clause}", values)
        total = cursor.fetchone()[0]
    
    return {'success': True, 'data': {'users': users, 'total': total}}

def suspend_user(user_id, admin_id, reason):
    """Suspend a user."""
    if not reason or len(reason) > 500:
        return {'success': False, 'error': 'Suspension reason must be between 1 and 500 characters'}
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET suspended = 1, suspended_reason = ?, suspended_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (reason, user_id))
        
        if cursor.rowcount == 0:
            return {'success': False, 'error': 'User not found'}
        
        # Log action
        cursor.execute("""
            INSERT INTO admin_logs (admin_id, action, target_table, target_id, details)
            VALUES (?, 'suspend_user', 'users', ?, ?)
        """, (admin_id, user_id, reason))
    
    return {'success': True, 'data': {'user_id': user_id}}

def unsuspend_user(user_id, admin_id):
    """Unsuspend a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE users
            SET suspended = 0, suspended_reason = NULL, suspended_at = NULL
            WHERE user_id = ?
        """, (user_id,))
        
        if cursor.rowcount == 0:
            return {'success': False, 'error': 'User not found'}
        
        # Log action
        cursor.execute("""
            INSERT INTO admin_logs (admin_id, action, target_table, target_id, details)
            VALUES (?, 'unsuspend_user', 'users', ?, 'User unsuspended')
        """, (admin_id, user_id))
    
    return {'success': True, 'data': {'user_id': user_id}}

def change_user_role(user_id, new_role, admin_id):
    """Change a user's role."""
    if new_role not in ['student', 'staff', 'admin']:
        return {'success': False, 'error': 'Invalid role'}
    
    # Prevent self-demotion
    if user_id == admin_id and new_role != 'admin':
        return {'success': False, 'error': 'Cannot remove your own admin role'}
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get current role
        cursor.execute("SELECT role FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        old_role = user['role']
        
        cursor.execute("""
            UPDATE users SET role = ? WHERE user_id = ?
        """, (new_role, user_id))
        
        # Log action
        cursor.execute("""
            INSERT INTO admin_logs (admin_id, action, target_table, target_id, details)
            VALUES (?, 'change_role', 'users', ?, ?)
        """, (admin_id, user_id, f"Changed from {old_role} to {new_role}"))
    
    return {'success': True, 'data': {'user_id': user_id, 'new_role': new_role}}

def delete_user(user_id, admin_id):
    """Delete a user and cascade effects."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            return {'success': False, 'error': 'User not found'}
        
        # Archive user's resources
        cursor.execute("""
            UPDATE resources SET status = 'archived' WHERE owner_id = ?
        """, (user_id,))
        
        # Cancel user's active bookings
        cursor.execute("""
            UPDATE bookings SET status = 'cancelled'
            WHERE requester_id = ? AND status IN ('pending', 'approved')
        """, (user_id,))
        
        # Delete user
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        
        # Log action
        cursor.execute("""
            INSERT INTO admin_logs (admin_id, action, target_table, target_id, details)
            VALUES (?, 'delete_user', 'users', ?, 'User deleted with cascade effects')
        """, (admin_id, user_id))
    
    return {'success': True, 'data': {'user_id': user_id}}

def get_admin_logs(admin_id=None, action=None, limit=50, offset=0):
    """Get admin action logs."""
    conditions = []
    values = []
    
    if admin_id:
        conditions.append("admin_id = ?")
        values.append(admin_id)
    
    if action:
        conditions.append("action = ?")
        values.append(action)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT al.*, u.name as admin_name, u.email as admin_email
            FROM admin_logs al
            JOIN users u ON al.admin_id = u.user_id
            WHERE {where_clause}
            ORDER BY al.timestamp DESC
            LIMIT ? OFFSET ?
        """, values + [limit, offset])
        
        logs = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute(f"SELECT COUNT(*) FROM admin_logs WHERE {where_clause}", values)
        total = cursor.fetchone()[0]
    
    return {'success': True, 'data': {'logs': logs, 'total': total}}

