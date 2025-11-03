"""
Resource management service.
"""
import json
import html
from src.data_access.database import get_db_connection

def sanitize_html(text, escape_html=False):
    """Remove HTML tags. Optionally escape HTML characters for titles/locations."""
    if not text:
        return text
    # Simple HTML tag removal
    import re
    text = re.sub(r'<[^>]+>', '', text)
    # Only escape HTML characters if requested (for titles/locations, not descriptions)
    if escape_html:
        return html.escape(text)
    return text

def create_resource(owner_id, title, description, category, location, capacity=None,
                   images=None, availability_rules=None, status='draft'):
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
    
    if status not in ['draft', 'published', 'archived']:
        return {'success': False, 'error': 'Invalid status'}
    
    # Sanitize inputs (escape for titles/locations, but allow special chars in descriptions)
    title = sanitize_html(title, escape_html=True)
    description = sanitize_html(description) if description else None  # Remove HTML tags but keep special chars
    location = sanitize_html(location, escape_html=True)
    
    # Handle images JSON
    images_json = json.dumps(images) if images else None
    
    # Handle availability_rules JSON
    availability_rules_json = json.dumps(availability_rules) if availability_rules else None
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO resources (owner_id, title, description, category, location, capacity, images, availability_rules, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (owner_id, title, description, category, location, capacity, images_json, availability_rules_json, status))
        
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
            if resource.get('images'):
                try:
                    resource['images'] = json.loads(resource['images'])
                except:
                    resource['images'] = []
            else:
                resource['images'] = []
            
            if resource.get('availability_rules'):
                try:
                    resource['availability_rules'] = json.loads(resource['availability_rules'])
                except:
                    resource['availability_rules'] = None
            
            # Unescape HTML entities in description (handles legacy data that was escaped)
            if resource.get('description'):
                try:
                    resource['description'] = html.unescape(resource['description'])
                except:
                    pass  # If unescaping fails, keep original
            
            return {'success': True, 'data': resource}
        return {'success': False, 'error': 'Resource not found'}

def update_resource(resource_id, owner_id=None, **kwargs):
    """Update a resource. Only owner or admin can update."""
    # Check if resource exists and user has permission
    resource_result = get_resource(resource_id)
    if not resource_result['success']:
        return resource_result
    
    resource = resource_result['data']
    
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
    
    # Build update query
    update_fields = []
    values = []
    
    for key, value in kwargs.items():
        if key in ['title', 'description', 'category', 'location', 'capacity', 'status', 'featured']:
            update_fields.append(f"{key} = ?")
            values.append(value)
        elif key == 'images':
            update_fields.append("images = ?")
            values.append(json.dumps(value) if value else None)
        elif key == 'availability_rules':
            update_fields.append("availability_rules = ?")
            values.append(json.dumps(value) if value else None)
    
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
                   keyword=None, location=None, limit=20, offset=0):
    """List resources with filters."""
    conditions = []
    values = []
    
    if status:
        conditions.append("status = ?")
        values.append(status)
    
    if category:
        conditions.append("category = ?")
        values.append(category)
    
    if owner_id:
        conditions.append("owner_id = ?")
        values.append(owner_id)
    
    if featured is not None:
        conditions.append("featured = ?")
        values.append(1 if featured else 0)
    
    if keyword:
        conditions.append("(title LIKE ? OR description LIKE ?)")
        keyword_pattern = f"%{keyword}%"
        values.extend([keyword_pattern, keyword_pattern])
    
    if location:
        conditions.append("location LIKE ?")
        values.append(f"%{location}%")
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM resources
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT ? OFFSET ?
        """, values + [limit, offset])
        
        rows = cursor.fetchall()
        
        resources = []
        for row in rows:
            resource = dict(row)
            # Parse JSON fields
            if resource.get('images'):
                try:
                    resource['images'] = json.loads(resource['images'])
                except:
                    resource['images'] = []
            if resource.get('availability_rules'):
                try:
                    resource['availability_rules'] = json.loads(resource['availability_rules'])
                except:
                    resource['availability_rules'] = None
            
            # Unescape HTML entities in description (handles legacy data that was escaped)
            if resource.get('description'):
                try:
                    resource['description'] = html.unescape(resource['description'])
                except:
                    pass  # If unescaping fails, keep original
            
            resources.append(resource)
        
        # Get total count
        cursor.execute(f"SELECT COUNT(*) FROM resources WHERE {where_clause}", values)
        total = cursor.fetchone()[0]
    
    return {'success': True, 'data': {'resources': resources, 'total': total}}

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
            if resource.get('images'):
                try:
                    resource['images'] = json.loads(resource['images'])
                except:
                    resource['images'] = []
            if resource.get('availability_rules'):
                try:
                    resource['availability_rules'] = json.loads(resource['availability_rules'])
                except:
                    resource['availability_rules'] = None
            
            # Unescape HTML entities in description (handles legacy data that was escaped)
            if resource.get('description'):
                try:
                    resource['description'] = html.unescape(resource['description'])
                except:
                    pass  # If unescaping fails, keep original
            
            resources.append(resource)
    
    return {'success': True, 'data': {'resources': resources}}

