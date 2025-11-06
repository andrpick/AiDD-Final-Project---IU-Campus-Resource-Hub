"""
Resource management service.
"""
from src.data_access.database import get_db_connection
from src.utils.json_utils import safe_json_dumps, parse_resource_json_fields
from src.utils.html_utils import sanitize_html, unescape_description

def convert_12_to_24_hour(hour_12, am_pm):
    """
    Convert 12-hour format to 24-hour format.
    
    Args:
        hour_12: Integer between 1-12
        am_pm: String 'AM' or 'PM'
    
    Returns:
        Integer between 0-23
    """
    if am_pm.upper() == 'AM':
        if hour_12 == 12:
            return 0  # 12 AM = 0:00
        return hour_12
    else:  # PM
        if hour_12 == 12:
            return 12  # 12 PM = 12:00
        return hour_12 + 12

def convert_24_to_12_hour(hour_24):
    """
    Convert 24-hour format to 12-hour format.
    
    Args:
        hour_24: Integer between 0-23
    
    Returns:
        Tuple of (hour_12, am_pm) where hour_12 is 1-12 and am_pm is 'AM' or 'PM'
    """
    if hour_24 == 0:
        return (12, 'AM')
    elif hour_24 < 12:
        return (hour_24, 'AM')
    elif hour_24 == 12:
        return (12, 'PM')
    else:
        return (hour_24 - 12, 'PM')

def create_resource(owner_id, title, description, category, location, capacity=None,
                   images=None, availability_rules=None, status='draft',
                   operating_hours_start=None, operating_hours_end=None, is_24_hours=False):
    """Create a new resource."""
    # Validate inputs
    if not title or len(title) < 5 or len(title) > 200:
        return {'success': False, 'error': 'Title must be between 5 and 200 characters'}
    
    if description and len(description) > 5000:
        return {'success': False, 'error': 'Description must be less than 5000 characters'}
    
    valid_categories = ['study_room', 'lab_equipment', 'av_equipment', 'event_space', 'tutoring', 'other']
    if category not in valid_categories:
        return {'success': False, 'error': 'Invalid category'}
    
    if not location or len(location) > 200:
        return {'success': False, 'error': 'Location must be less than 200 characters'}
    
    # Capacity is optional - if provided, it must be a positive integer
    if capacity is not None:
        if not isinstance(capacity, int) or capacity < 1:
            return {'success': False, 'error': 'Capacity must be at least 1 if provided'}
    
    # Operating hours validation - skip if 24 hours
    if not is_24_hours:
        if operating_hours_start is None or operating_hours_end is None:
            return {'success': False, 'error': 'Operating hours are required'}
        
        if not isinstance(operating_hours_start, int) or not isinstance(operating_hours_end, int):
            return {'success': False, 'error': 'Operating hours must be integers'}
        
        if operating_hours_start < 0 or operating_hours_start > 23:
            return {'success': False, 'error': 'Operating hours start must be between 0 and 23'}
        
        if operating_hours_end < 0 or operating_hours_end > 23:
            return {'success': False, 'error': 'Operating hours end must be between 0 and 23'}
        
        if operating_hours_start >= operating_hours_end:
            return {'success': False, 'error': 'Operating hours start must be before end'}
    else:
        # For 24-hour operation, set hours to 0-23 (full day)
        operating_hours_start = 0
        operating_hours_end = 23
    
    if status not in ['draft', 'published', 'archived']:
        return {'success': False, 'error': 'Invalid status'}
    
    # Sanitize inputs (escape for titles/locations, but allow special chars in descriptions)
    title = sanitize_html(title, escape_html=True)
    description = sanitize_html(description) if description else None  # Remove HTML tags but keep special chars
    location = sanitize_html(location, escape_html=True)
    
    # Handle images JSON
    images_json = safe_json_dumps(images)
    
    # Handle availability_rules JSON
    availability_rules_json = safe_json_dumps(availability_rules)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO resources (owner_id, title, description, category, location, capacity, images, availability_rules, status, operating_hours_start, operating_hours_end, is_24_hours)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (owner_id, title, description, category, location, capacity, images_json, availability_rules_json, status, operating_hours_start, operating_hours_end, 1 if is_24_hours else 0))
        
        resource_id = cursor.lastrowid
    
    return {'success': True, 'data': {'resource_id': resource_id}}

def get_resource(resource_id):
    """Get a resource by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resources WHERE resource_id = ?", (resource_id,))
        row = cursor.fetchone()
        
        if row:
            resource = dict(row)
            # Parse JSON fields
            resource = parse_resource_json_fields(resource)
            
            # Unescape HTML entities in description (handles legacy data that was escaped)
            if resource.get('description'):
                resource['description'] = unescape_description(resource['description'])
            
            return {'success': True, 'data': resource}
        return {'success': False, 'error': 'Resource not found'}

def update_resource(resource_id, owner_id=None, **kwargs):
    """Update a resource. Only owner or admin can update.
    
    Note: owner_id cannot be updated through this function. Use reassign_resource_ownership()
    for admin-only ownership transfers.
    """
    # Check if resource exists and user has permission
    resource_result = get_resource(resource_id)
    if not resource_result['success']:
        return resource_result
    
    resource = resource_result['data']
    
    # Explicitly prevent owner_id updates through this function
    if owner_id is not None and owner_id != resource['owner_id']:
        return {'success': False, 'error': 'Owner ID cannot be changed through this function. Only administrators can reassign resource ownership.'}
    
    # Permission check will be done in controller
    # Validate update fields
    if 'title' in kwargs:
        if not kwargs['title'] or len(kwargs['title']) < 5 or len(kwargs['title']) > 200:
            return {'success': False, 'error': 'Title must be between 5 and 200 characters'}
        kwargs['title'] = sanitize_html(kwargs['title'], escape_html=True)
    
    if 'description' in kwargs:
        if kwargs['description'] and len(kwargs['description']) > 5000:
            return {'success': False, 'error': 'Description must be less than 5000 characters'}
        kwargs['description'] = sanitize_html(kwargs['description']) if kwargs.get('description') else None  # Remove HTML tags but keep special chars
    
    if 'location' in kwargs:
        if not kwargs['location'] or len(kwargs['location']) > 200:
            return {'success': False, 'error': 'Location must be less than 200 characters'}
        kwargs['location'] = sanitize_html(kwargs['location'], escape_html=True)
    
    if 'capacity' in kwargs:
        # Capacity is optional - if provided, it must be a positive integer; if None, allow it
        if kwargs['capacity'] is not None:
            if not isinstance(kwargs['capacity'], int) or kwargs['capacity'] < 1:
                return {'success': False, 'error': 'Capacity must be at least 1 if provided'}
    
    # Operating hours validation - both must be provided together if updating (unless 24 hours)
    if 'is_24_hours' in kwargs:
        is_24_hours = kwargs['is_24_hours']
        if is_24_hours:
            # For 24-hour operation, set hours to 0-23 (full day)
            kwargs['operating_hours_start'] = 0
            kwargs['operating_hours_end'] = 23
    
    if 'operating_hours_start' in kwargs or 'operating_hours_end' in kwargs:
        # If one is provided, both must be provided (unless 24 hours)
        if 'operating_hours_start' not in kwargs or 'operating_hours_end' not in kwargs:
            # Check if this is a 24-hour operation
            is_24_hours = kwargs.get('is_24_hours', False)
            if not is_24_hours:
                return {'success': False, 'error': 'Both operating hours start and end must be provided'}
        
        operating_start = kwargs['operating_hours_start']
        operating_end = kwargs['operating_hours_end']
        is_24_hours = kwargs.get('is_24_hours', False)
        
        if not is_24_hours:
            if not isinstance(operating_start, int) or not isinstance(operating_end, int):
                return {'success': False, 'error': 'Operating hours must be integers'}
            
            if operating_start < 0 or operating_start > 23:
                return {'success': False, 'error': 'Operating hours start must be between 0 and 23'}
            
            if operating_end < 0 or operating_end > 23:
                return {'success': False, 'error': 'Operating hours end must be between 0 and 23'}
            
            if operating_start >= operating_end:
                return {'success': False, 'error': 'Operating hours start must be before end'}
    
    # Build update query
    update_fields = []
    values = []
    
    for key, value in kwargs.items():
        if key in ['title', 'description', 'category', 'location', 'capacity', 'status', 'featured', 'operating_hours_start', 'operating_hours_end', 'is_24_hours']:
            update_fields.append(f"{key} = ?")
            # Convert boolean to int for is_24_hours
            if key == 'is_24_hours':
                values.append(1 if value else 0)
            else:
                values.append(value)
        elif key == 'images':
            update_fields.append("images = ?")
            values.append(safe_json_dumps(value))
        elif key == 'availability_rules':
            update_fields.append("availability_rules = ?")
            values.append(safe_json_dumps(value))
    
    if not update_fields:
        return {'success': False, 'error': 'No valid fields to update'}
    
    update_fields.append("updated_at = CURRENT_TIMESTAMP")
    values.append(resource_id)
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE resources SET {', '.join(update_fields)}
            WHERE resource_id = ?
        """, values)
    
    return {'success': True, 'data': {'resource_id': resource_id}}

def delete_resource(resource_id):
    """Soft delete a resource (set status to archived)."""
    return update_resource(resource_id, status='archived')

def list_resources(status='published', category=None, owner_id=None, featured=None, 
                   keyword=None, location=None, is_24_hours=None, sort_by=None, sort_order='desc',
                   limit=20, offset=0):
    """List resources with filters and sorting."""
    conditions = []
    values = []
    
    if status:
        conditions.append("r.status = ?")
        values.append(status)
    
    if category:
        conditions.append("r.category = ?")
        values.append(category)
    
    if owner_id:
        conditions.append("r.owner_id = ?")
        values.append(owner_id)
    
    if featured is not None:
        conditions.append("r.featured = ?")
        values.append(1 if featured else 0)
    
    if keyword:
        conditions.append("(r.title LIKE ? OR r.description LIKE ?)")
        keyword_pattern = f"%{keyword}%"
        values.extend([keyword_pattern, keyword_pattern])
    
    if location:
        conditions.append("r.location LIKE ?")
        values.append(f"%{location}%")
    
    if is_24_hours is not None:
        conditions.append("r.is_24_hours = ?")
        values.append(1 if is_24_hours else 0)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    # Determine sort field and build query
    valid_sort_fields = {
        'booking_count': 'booking_count',
        'avg_rating': 'avg_rating',
        'recently_booked': 'recent_booking_date',
        'created_at': 'r.created_at',
        'title': 'r.title'
    }
    
    sort_field = valid_sort_fields.get(sort_by, 'r.created_at')
    sort_direction = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
    
    # Build query based on sort type
    if sort_by in ['booking_count', 'avg_rating', 'recently_booked']:
        # Need JOINs for statistics-based sorting
        query = f"""
            SELECT r.*,
                   COUNT(DISTINCT b.booking_id) as booking_count,
                   AVG(rev.rating) as avg_rating,
                   MAX(b.created_at) as recent_booking_date
            FROM resources r
            LEFT JOIN bookings b ON r.resource_id = b.resource_id
            LEFT JOIN reviews rev ON r.resource_id = rev.resource_id
            WHERE {where_clause}
            GROUP BY r.resource_id
            ORDER BY {sort_field} {sort_direction}, r.created_at DESC
            LIMIT ? OFFSET ?
        """
    else:
        # Simple query for non-statistics sorting
        query = f"""
            SELECT * FROM resources r
            WHERE {where_clause}
            ORDER BY {sort_field} {sort_direction}
            LIMIT ? OFFSET ?
        """
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, values + [limit, offset])
        
        rows = cursor.fetchall()
        
        resources = []
        for row in rows:
            resource = dict(row)
            # Parse JSON fields
            resource = parse_resource_json_fields(resource)
            
            # Unescape HTML entities in description (handles legacy data that was escaped)
            if resource.get('description'):
                resource['description'] = unescape_description(resource['description'])
            
            # Handle computed fields
            if resource.get('avg_rating'):
                resource['avg_rating'] = float(resource['avg_rating'])
            else:
                resource['avg_rating'] = None
            
            if resource.get('booking_count') is None:
                resource['booking_count'] = 0
            
            resources.append(resource)
        
        # Get total count (using same WHERE clause but without JOINs for count)
        count_query = f"SELECT COUNT(*) FROM resources r WHERE {where_clause}"
        cursor.execute(count_query, values)
        total = cursor.fetchone()[0]
    
    return {'success': True, 'data': {'resources': resources, 'total': total}}

def reassign_resource_ownership(resource_id, new_owner_id, admin_id):
    """Reassign resource ownership to a new user. Admin only."""
    # Verify admin_id is actually an admin
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT role FROM users WHERE user_id = ?", (admin_id,))
        admin_user = cursor.fetchone()
        
        if not admin_user:
            return {'success': False, 'error': 'Admin user not found'}
        
        if admin_user['role'] != 'admin':
            return {'success': False, 'error': 'Only administrators can reassign resource ownership'}
    
    # Check if resource exists
    resource_result = get_resource(resource_id)
    if not resource_result['success']:
        return {'success': False, 'error': 'Resource not found'}
    
    resource = resource_result['data']
    
    # Check if new owner exists and is not deleted
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, deleted FROM users WHERE user_id = ?", (new_owner_id,))
        new_owner = cursor.fetchone()
        
        if not new_owner:
            return {'success': False, 'error': 'New owner not found'}
        
        if new_owner['deleted']:
            return {'success': False, 'error': 'Cannot assign resource to deleted user'}
        
        # Check if resource is already owned by this user
        if resource['owner_id'] == new_owner_id:
            return {'success': False, 'error': 'Resource is already owned by this user'}
        
        # Get old owner info for logging
        old_owner_id = resource['owner_id']
        cursor.execute("SELECT name, email, deleted FROM users WHERE user_id = ?", (old_owner_id,))
        old_owner = cursor.fetchone()
        old_owner_name = '[Deleted User]' if (old_owner and old_owner['deleted']) else (old_owner['name'] if old_owner else 'Unknown')
        
        # Get new owner name for logging
        cursor.execute("SELECT name FROM users WHERE user_id = ?", (new_owner_id,))
        new_owner_info = cursor.fetchone()
        new_owner_name = new_owner_info['name'] if new_owner_info else 'Unknown'
        
        # Update resource ownership
        cursor.execute("""
            UPDATE resources 
            SET owner_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE resource_id = ?
        """, (new_owner_id, resource_id))
        
        # Log action
        cursor.execute("""
            INSERT INTO admin_logs (admin_id, action, target_table, target_id, details)
            VALUES (?, 'reassign_resource_ownership', 'resources', ?, ?)
        """, (admin_id, resource_id, f"Reassigned from {old_owner_name} (user_id: {old_owner_id}) to {new_owner_name} (user_id: {new_owner_id})"))
        
        conn.commit()
    
    return {'success': True, 'data': {'resource_id': resource_id, 'new_owner_id': new_owner_id}}

def get_featured_resources(limit=6):
    """Get featured resources for homepage."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM resources
            WHERE featured = 1 AND status = 'published'
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        
        rows = cursor.fetchall()
        
        resources = []
        for row in rows:
            resource = dict(row)
            # Parse JSON fields
            resource = parse_resource_json_fields(resource)
            
            # Unescape HTML entities in description (handles legacy data that was escaped)
            if resource.get('description'):
                resource['description'] = unescape_description(resource['description'])
            
            resources.append(resource)
    
    return {'success': True, 'data': {'resources': resources}}

