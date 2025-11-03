"""
Search and filtering service.
"""
import json
from src.data_access.database import get_db_connection

def search_resources(keyword=None, category=None, location=None, capacity_min=None,
                    capacity_max=None, available_from=None, available_to=None,
                    sort_by='created_at', sort_order='desc', page=1, page_size=20):
    """Search resources with filters and sorting."""
    # Validate pagination
    page = max(1, int(page))
    page_size = min(100, max(1, int(page_size)))
    offset = (page - 1) * page_size
    
    # Build query
    conditions = ["status = 'published'"]
    values = []
    
    # Keyword search
    if keyword:
        conditions.append("(title LIKE ? OR description LIKE ?)")
        keyword_pattern = f"%{keyword}%"
        values.extend([keyword_pattern, keyword_pattern])
    
    # Category filter
    if category:
        conditions.append("category = ?")
        values.append(category)
    
    # Location filter
    if location:
        conditions.append("location LIKE ?")
        values.append(f"%{location}%")
    
    # Capacity filters
    if capacity_min:
        conditions.append("capacity >= ?")
        values.append(int(capacity_min))
    
    if capacity_max:
        conditions.append("capacity <= ?")
        values.append(int(capacity_max))
    
    where_clause = " AND ".join(conditions)
    
    # Sorting
    valid_sort_fields = {
        'relevance': 'created_at',  # Simple implementation
        'created_at': 'created_at',
        'title': 'title',
        'capacity': 'capacity',
        'rating': 'rating'  # Would need JOIN with reviews table
    }
    
    sort_field = valid_sort_fields.get(sort_by, 'created_at')
    sort_direction = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
    
    # Availability check would require JOIN with bookings table
    # For now, we'll do basic filtering
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get resources
        query = f"""
            SELECT r.*, 
                   AVG(rev.rating) as avg_rating,
                   COUNT(rev.review_id) as review_count
            FROM resources r
            LEFT JOIN reviews rev ON r.resource_id = rev.resource_id
            WHERE {where_clause}
            GROUP BY r.resource_id
            ORDER BY {sort_field} {sort_direction}
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(query, values + [page_size, offset])
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
            
            # Handle rating
            if resource.get('avg_rating'):
                resource['avg_rating'] = float(resource['avg_rating'])
            else:
                resource['avg_rating'] = None
            
            resources.append(resource)
        
        # Get total count
        count_query = f"""
            SELECT COUNT(DISTINCT r.resource_id)
            FROM resources r
            WHERE {where_clause}
        """
        cursor.execute(count_query, values)
        total = cursor.fetchone()[0]
    
    return {
        'success': True,
        'data': {
            'resources': resources,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
    }

