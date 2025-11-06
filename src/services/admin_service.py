"""
Admin service for user management and statistics.
"""
from src.data_access.database import get_db_connection

def get_statistics(category_filter=None, location_filter=None, featured_filter=None, sort_by='booking_count', sort_order='desc'):
    """Get system statistics for admin dashboard."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # User statistics (exclude deleted users)
        cursor.execute("""
            SELECT role, COUNT(*) as count
            FROM users
            WHERE suspended = 0 AND (deleted = 0 OR deleted IS NULL)
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
        
        # Reviews by rating
        cursor.execute("""
            SELECT rating, COUNT(*) as count
            FROM reviews
            GROUP BY rating
            ORDER BY rating DESC
        """)
        reviews_by_rating = {row['rating']: row['count'] for row in cursor.fetchall()}
        
        # Active users in last 30 days (users with bookings or reviews, excluding deleted users)
        cursor.execute("""
            SELECT COUNT(DISTINCT user_id) as count
            FROM (
                SELECT requester_id as user_id FROM bookings b
                JOIN users u ON b.requester_id = u.user_id
                WHERE b.created_at >= datetime('now', '-30 days')
                AND (u.deleted = 0 OR u.deleted IS NULL)
                UNION
                SELECT reviewer_id as user_id FROM reviews r
                JOIN users u ON r.reviewer_id = u.user_id
                WHERE r.timestamp >= datetime('now', '-30 days')
                AND (u.deleted = 0 OR u.deleted IS NULL)
            )
        """)
        active_users = cursor.fetchone()['count']
        
        # Build filter conditions for popular resources
        filter_conditions = ["r.status = 'published'"]
        filter_values = []
        
        if category_filter:
            filter_conditions.append("r.category = ?")
            filter_values.append(category_filter)
        
        if location_filter:
            filter_conditions.append("r.location LIKE ?")
            filter_values.append(f"%{location_filter}%")
        
        if featured_filter is not None:
            filter_conditions.append("r.featured = ?")
            filter_values.append(1 if featured_filter else 0)
        
        where_clause = " AND ".join(filter_conditions)
        
        # Validate sort parameters
        valid_sort_fields = ['booking_count', 'review_count', 'avg_rating', 'title', 'category', 'location']
        if sort_by not in valid_sort_fields:
            sort_by = 'booking_count'
        
        if sort_order.lower() not in ['asc', 'desc']:
            sort_order = 'desc'
        
        sort_direction = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
        
        # Popular resources (most booked) with additional statistics and filters
        query = f"""
            SELECT 
                r.resource_id, 
                r.title, 
                r.category,
                r.location,
                r.capacity,
                r.featured,
                COUNT(DISTINCT b.booking_id) as booking_count,
                COUNT(DISTINCT rev.review_id) as review_count,
                AVG(rev.rating) as avg_rating
            FROM resources r
            LEFT JOIN bookings b ON r.resource_id = b.resource_id AND b.status = 'approved'
            LEFT JOIN reviews rev ON r.resource_id = rev.resource_id
            WHERE {where_clause}
            GROUP BY r.resource_id, r.title, r.category, r.location, r.capacity, r.featured
            ORDER BY {sort_by} {sort_direction}, booking_count DESC
            LIMIT 10
        """
        cursor.execute(query, filter_values)
        popular_resources_raw = cursor.fetchall()
        
        # Process popular resources
        popular_resources = []
        for row in popular_resources_raw:
            resource = dict(row)
            # Handle rating
            if resource.get('avg_rating'):
                resource['avg_rating'] = float(resource['avg_rating'])
            else:
                resource['avg_rating'] = None
            popular_resources.append(resource)
        
        # Get unique categories and locations for filter dropdowns
        cursor.execute("""
            SELECT DISTINCT category 
            FROM resources 
            WHERE status = 'published'
            ORDER BY category
        """)
        available_categories = [row['category'] for row in cursor.fetchall()]
        
        cursor.execute("""
            SELECT DISTINCT location 
            FROM resources 
            WHERE status = 'published'
            ORDER BY location
        """)
        available_locations = [row['location'] for row in cursor.fetchall()]
    
    return {
        'success': True,
        'data': {
            'users_by_role': users_by_role,
            'resources_by_category_status': resources_by_category_status,
            'resources_by_status': resources_by_status,
            'bookings_by_status': bookings_by_status,
            'total_bookings': total_bookings,
            'total_reviews': total_reviews,
            'reviews_by_rating': reviews_by_rating,
            'active_users_30_days': active_users,
            'popular_resources': popular_resources,
            'available_categories': available_categories,
            'available_locations': available_locations
        }
    }

def list_users(role=None, suspended=None, department=None, search=None, limit=20, offset=0, include_deleted=False):
    """List users with filters. By default, excludes deleted users."""
    conditions = []
    values = []
    
    # Exclude deleted users by default
    if not include_deleted:
        conditions.append("(deleted = 0 OR deleted IS NULL)")
    
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
            SELECT user_id, name, email, role, department, suspended, created_at, deleted, deleted_at
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
        # Check if user exists and is not deleted
        cursor.execute("SELECT user_id, deleted FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return {'success': False, 'error': 'User not found'}
        if user['deleted']:
            return {'success': False, 'error': 'Cannot suspend deleted user'}
        
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
        """, (admin_id, user_id, f"User suspended. Reason: {reason}"))
        conn.commit()
    
    return {'success': True, 'data': {'user_id': user_id}}

def unsuspend_user(user_id, admin_id):
    """Unsuspend a user."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Check if user exists and is not deleted
        cursor.execute("SELECT user_id, deleted FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return {'success': False, 'error': 'User not found'}
        if user['deleted']:
            return {'success': False, 'error': 'Cannot unsuspend deleted user'}
        
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
        conn.commit()
    
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
        
        # Get current role and check if user exists and is not deleted
        cursor.execute("SELECT role, deleted FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        if user['deleted']:
            return {'success': False, 'error': 'Cannot change role of deleted user'}
        
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
    """Soft delete a user and cascade effects."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if user exists and is not already deleted
        cursor.execute("SELECT user_id, deleted FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        if user['deleted']:
            return {'success': False, 'error': 'User is already deleted'}
        
        # Archive user's resources
        cursor.execute("""
            UPDATE resources SET status = 'archived' WHERE owner_id = ?
        """, (user_id,))
        
        # Cancel user's active bookings
        cursor.execute("""
            UPDATE bookings SET status = 'cancelled'
            WHERE requester_id = ? AND status IN ('approved')
        """, (user_id,))
        
        # Soft delete user: anonymize PII but keep the record
        cursor.execute("""
            UPDATE users 
            SET deleted = 1,
                deleted_at = CURRENT_TIMESTAMP,
                deleted_by = ?,
                email = NULL,
                name = '[Deleted User]',
                password_hash = '',
                department = NULL,
                profile_image = NULL,
                suspended = 0,
                suspended_reason = NULL,
                suspended_at = NULL
            WHERE user_id = ?
        """, (admin_id, user_id))
        
        # Log action
        cursor.execute("""
            INSERT INTO admin_logs (admin_id, action, target_table, target_id, details)
            VALUES (?, 'delete_user', 'users', ?, 'User soft deleted with cascade effects')
        """, (admin_id, user_id))
        
        conn.commit()
    
    return {'success': True, 'data': {'user_id': user_id}}

def get_user(user_id):
    """Get a single user by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, name, email, role, department, profile_image, 
                   created_at, suspended, suspended_reason, suspended_at,
                   deleted, deleted_at, deleted_by
            FROM users
            WHERE user_id = ?
        """, (user_id,))
        
        row = cursor.fetchone()
        if not row:
            return {'success': False, 'error': 'User not found'}
        
        return {'success': True, 'data': dict(row)}

def get_deleted_users(limit=100, offset=0):
    """Get all soft-deleted users for restore management."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT user_id, name, email, role, department, deleted_at, deleted_by
            FROM users
            WHERE deleted = 1
            ORDER BY deleted_at DESC
            LIMIT ? OFFSET ?
        """, (limit, offset))
        
        users = [dict(row) for row in cursor.fetchall()]
        
        # Get total count
        cursor.execute("SELECT COUNT(*) FROM users WHERE deleted = 1")
        total = cursor.fetchone()[0]
        
        # Get admin names who deleted users
        for user in users:
            if user['deleted_by']:
                cursor.execute("SELECT name FROM users WHERE user_id = ?", (user['deleted_by'],))
                admin = cursor.fetchone()
                user['deleted_by_name'] = admin['name'] if admin else '[Unknown]'
            else:
                user['deleted_by_name'] = None
    
    return {'success': True, 'data': {'users': users, 'total': total}}

def restore_user(user_id, admin_id):
    """Restore a soft-deleted user. Note: PII (email, name, password) was anonymized and cannot be automatically restored."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if user exists and is deleted
        cursor.execute("SELECT user_id, deleted FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        if not user['deleted']:
            return {'success': False, 'error': 'User is not deleted'}
        
        # Restore user: clear deleted flags (but PII remains anonymized)
        cursor.execute("""
            UPDATE users 
            SET deleted = 0,
                deleted_at = NULL,
                deleted_by = NULL
            WHERE user_id = ?
        """, (user_id,))
        
        # Log action
        cursor.execute("""
            INSERT INTO admin_logs (admin_id, action, target_table, target_id, details)
            VALUES (?, 'restore_user', 'users', ?, 'User restored from soft delete. Note: PII (email, name, password) was anonymized and needs manual restoration.')
        """, (admin_id, user_id))
        
        conn.commit()
    
    return {'success': True, 'data': {'user_id': user_id}}

def update_user(user_id, admin_id, name=None, email=None, password=None, role=None, 
                department=None, profile_image=None, suspended=None, suspended_reason=None):
    """Update user information. Admin can update any field."""
    import bcrypt
    from src.services.auth_service import validate_email, validate_password, validate_name
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Check if user exists and is not deleted
        cursor.execute("SELECT user_id, email, deleted FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return {'success': False, 'error': 'User not found'}
        
        if user['deleted']:
            return {'success': False, 'error': 'Cannot update deleted user'}
        
        current_email = user['email']
        changes = []
        
        # Build update query dynamically
        updates = []
        values = []
        
        if name is not None:
            name_valid, name_msg = validate_name(name)
            if not name_valid:
                return {'success': False, 'error': name_msg}
            updates.append("name = ?")
            values.append(name)
            changes.append(f"name: {name}")
        
        if email is not None and email != current_email:
            if not validate_email(email):
                return {'success': False, 'error': 'Invalid email format'}
            # Check if new email already exists
            cursor.execute("SELECT user_id FROM users WHERE email = ? AND user_id != ?", 
                         (email.lower(), user_id))
            if cursor.fetchone():
                return {'success': False, 'error': 'Email already registered'}
            updates.append("email = ?")
            values.append(email.lower())
            changes.append(f"email: {email.lower()}")
        
        if password is not None and password.strip():
            password_valid, password_msg = validate_password(password)
            if not password_valid:
                return {'success': False, 'error': password_msg}
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(12)).decode('utf-8')
            updates.append("password_hash = ?")
            values.append(password_hash)
            changes.append("password: [updated]")
        elif password is not None and not password.strip():
            # Empty password string means don't change password
            pass
        
        if role is not None:
            if role not in ['student', 'staff', 'admin']:
                return {'success': False, 'error': 'Invalid role'}
            # Prevent self-demotion
            if user_id == admin_id and role != 'admin':
                return {'success': False, 'error': 'Cannot remove your own admin role'}
            updates.append("role = ?")
            values.append(role)
            changes.append(f"role: {role}")
        
        if department is not None:
            # Allow empty string to clear department
            if len(department) > 100:
                return {'success': False, 'error': 'Department name too long (max 100 characters)'}
            updates.append("department = ?")
            values.append(department.strip() if department.strip() else None)
            changes.append(f"department: {department or 'cleared'}")
        
        if profile_image is not None:
            updates.append("profile_image = ?")
            values.append(profile_image.strip() if profile_image.strip() else None)
            changes.append(f"profile_image: {profile_image or 'cleared'}")
        
        if suspended is not None:
            updates.append("suspended = ?")
            values.append(1 if suspended else 0)
            if suspended:
                updates.append("suspended_at = CURRENT_TIMESTAMP")
                if suspended_reason:
                    updates.append("suspended_reason = ?")
                    values.append(suspended_reason)
                    changes.append(f"suspended: True (reason: {suspended_reason[:50]})")
                else:
                    changes.append("suspended: True")
            else:
                updates.append("suspended_reason = NULL")
                updates.append("suspended_at = NULL")
                changes.append("suspended: False")
        
        if not updates:
            return {'success': False, 'error': 'No changes provided'}
        
        # Add user_id for WHERE clause
        values.append(user_id)
        
        # Execute update
        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
        cursor.execute(query, values)
        
        if cursor.rowcount == 0:
            return {'success': False, 'error': 'Failed to update user'}
        
        # Log action
        details = f"Updated user fields: {', '.join(changes)}"
        cursor.execute("""
            INSERT INTO admin_logs (admin_id, action, target_table, target_id, details)
            VALUES (?, 'update_user', 'users', ?, ?)
        """, (admin_id, user_id, details))
        conn.commit()
    
    return {'success': True, 'data': {'user_id': user_id}}

def get_admin_logs(admin_id=None, action=None, target_table=None, limit=50, offset=0):
    """Get admin action logs with target names."""
    conditions = []
    values = []
    
    if admin_id:
        conditions.append("al.admin_id = ?")
        values.append(admin_id)
    
    if action:
        conditions.append("al.action = ?")
        values.append(action)
    
    if target_table:
        conditions.append("al.target_table = ?")
        values.append(target_table)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT al.*, u.name as admin_name, u.email as admin_email
            FROM admin_logs al
            LEFT JOIN users u ON al.admin_id = u.user_id AND (u.deleted = 0 OR u.deleted IS NULL)
            WHERE {where_clause}
            ORDER BY al.timestamp DESC
            LIMIT ? OFFSET ?
        """, values + [limit, offset])
        
        logs = [dict(row) for row in cursor.fetchall()]
        
        # Enrich logs with target names
        for log in logs:
            target_id = log['target_id']
            target_table_name = log['target_table']
            
            # Handle admin name (may be deleted)
            if not log.get('admin_name'):
                log['admin_name'] = '[Deleted User]'
            if not log.get('admin_email'):
                log['admin_email'] = '[Deleted]'
            
            if target_table_name == 'users':
                cursor.execute("SELECT name, email FROM users WHERE user_id = ?", (target_id,))
                target_row = cursor.fetchone()
                if target_row:
                    log['target_name'] = target_row['name'] or '[Deleted User]'
                    log['target_email'] = target_row['email'] or '[Deleted]'
            elif target_table_name == 'resources':
                cursor.execute("SELECT title FROM resources WHERE resource_id = ?", (target_id,))
                target_row = cursor.fetchone()
                if target_row:
                    log['target_name'] = target_row['title']
            elif target_table_name == 'bookings':
                # Get booking info and resource name
                cursor.execute("""
                    SELECT b.start_datetime, b.end_datetime, b.status, r.title as resource_title
                    FROM bookings b
                    LEFT JOIN resources r ON b.resource_id = r.resource_id
                    WHERE b.booking_id = ?
                """, (target_id,))
                target_row = cursor.fetchone()
                if target_row:
                    log['target_name'] = target_row['resource_title'] or f"Booking #{target_id}"
                    log['target_booking_info'] = {
                        'start_datetime': target_row['start_datetime'],
                        'end_datetime': target_row['end_datetime'],
                        'status': target_row['status']
                    }
        
        cursor.execute(f"SELECT COUNT(*) FROM admin_logs al WHERE {where_clause}", values)
        total = cursor.fetchone()[0]
    
    return {'success': True, 'data': {'logs': logs, 'total': total}}

