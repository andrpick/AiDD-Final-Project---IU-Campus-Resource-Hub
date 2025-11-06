"""
Search and filtering service.
"""
import json
from datetime import datetime, date, time
from src.data_access.database import get_db_connection
from dateutil.tz import gettz, tzutc
from dateutil import parser

def search_resources(keyword=None, category=None, location=None, capacity_min=None,
                    capacity_max=None, available_from=None, available_to=None,
                    available_date=None, available_start_time=None, available_end_time=None,
                    sort_by='created_at', sort_order='desc', page=1, page_size=20):
    """Search resources with filters and sorting."""
    # Validate pagination
    page = max(1, int(page))
    page_size = min(100, max(1, int(page_size)))
    offset = (page - 1) * page_size
    
    # Build query
    conditions = ["r.status = 'published'"]
    values = []
    
    # Keyword search
    if keyword:
        conditions.append("(r.title LIKE ? OR r.description LIKE ?)")
        keyword_pattern = f"%{keyword}%"
        values.extend([keyword_pattern, keyword_pattern])
    
    # Category filter
    if category:
        conditions.append("r.category = ?")
        values.append(category)
    
    # Location filter
    if location:
        conditions.append("r.location = ?")
        values.append(location)
    
    # Capacity filters
    if capacity_min:
        conditions.append("r.capacity >= ?")
        values.append(int(capacity_min))
    
    if capacity_max:
        conditions.append("r.capacity <= ?")
        values.append(int(capacity_max))
    
    # Availability filter - check date and time range
    availability_filter_applied = False
    if available_date and available_start_time and available_end_time:
        try:
            # Parse date (YYYY-MM-DD format)
            filter_date = datetime.strptime(available_date, '%Y-%m-%d').date()
            
            # Parse time strings (HH:MM format)
            start_time_parts = available_start_time.split(':')
            end_time_parts = available_end_time.split(':')
            start_hour = int(start_time_parts[0])
            start_minute = int(start_time_parts[1]) if len(start_time_parts) > 1 else 0
            end_hour = int(end_time_parts[0])
            end_minute = int(end_time_parts[1]) if len(end_time_parts) > 1 else 0
            
            # Convert to EST timezone datetime objects
            est_tz = gettz('America/New_York')
            start_datetime_est = datetime.combine(filter_date, time(start_hour, start_minute)).replace(tzinfo=est_tz)
            end_datetime_est = datetime.combine(filter_date, time(end_hour, end_minute)).replace(tzinfo=est_tz)
            
            # Convert to UTC for database comparison
            start_datetime_utc = start_datetime_est.astimezone(tzutc())
            end_datetime_utc = end_datetime_est.astimezone(tzutc())
            
            availability_filter_applied = True
        except (ValueError, TypeError) as e:
            # Invalid date/time format, skip availability filter
            availability_filter_applied = False
    
    where_clause = " AND ".join(conditions)
    
    # Sorting
    valid_sort_fields = {
        'relevance': 'r.created_at',  # Simple implementation
        'created_at': 'r.created_at',
        'title': 'r.title',
        'capacity': 'r.capacity',
        'booking_count': 'booking_count',
        'avg_rating': 'avg_rating',
        'recently_booked': 'recent_booking_date',
        'rating': 'avg_rating'  # Alias for avg_rating
    }
    
    sort_field = valid_sort_fields.get(sort_by, 'r.created_at')
    sort_direction = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
    
    # Build query based on sort type
    if sort_by in ['booking_count', 'avg_rating', 'recently_booked', 'rating']:
        # Need JOINs for statistics-based sorting
        query = f"""
            SELECT r.*, 
                   COUNT(DISTINCT b.booking_id) as booking_count,
                   AVG(rev.rating) as avg_rating,
                   MAX(b.created_at) as recent_booking_date,
                   COUNT(rev.review_id) as review_count
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
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
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
            
            # Handle booking_count
            if resource.get('booking_count') is None:
                resource['booking_count'] = 0
            
            # Check availability if filter is applied
            if availability_filter_applied:
                is_available = check_resource_availability_for_time(
                    cursor, resource['resource_id'], 
                    start_datetime_utc, end_datetime_utc,
                    resource.get('operating_hours_start'),
                    resource.get('operating_hours_end'),
                    resource.get('is_24_hours')
                )
                if not is_available:
                    continue  # Skip this resource if not available
            
            resources.append(resource)
        
        # Get total count - need to re-check if availability filter was applied
        if availability_filter_applied:
            # Re-run query to get accurate count with availability filter
            # Need to fetch resource_id and operating hours fields for availability check
            count_query = f"""
                SELECT r.resource_id, r.operating_hours_start, r.operating_hours_end, r.is_24_hours
                FROM resources r
                WHERE {where_clause}
            """
            cursor.execute(count_query, values)
            all_resources_raw = cursor.fetchall()
            total = 0
            for row in all_resources_raw:
                resource = dict(row)
                is_available = check_resource_availability_for_time(
                    cursor, resource['resource_id'], 
                    start_datetime_utc, end_datetime_utc,
                    resource.get('operating_hours_start'),
                    resource.get('operating_hours_end'),
                    resource.get('is_24_hours')
                )
                if is_available:
                    total += 1
        else:
            count_query = f"""
                SELECT COUNT(*)
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


def check_resource_availability_for_time(cursor, resource_id, start_datetime_utc, end_datetime_utc,
                                          operating_hours_start, operating_hours_end, is_24_hours):
    """
    Check if a resource is available during a specific time range.
    
    Args:
        cursor: Database cursor
        resource_id: Resource ID to check
        start_datetime_utc: Start datetime in UTC
        end_datetime_utc: End datetime in UTC
        operating_hours_start: Resource operating hours start (0-23)
        operating_hours_end: Resource operating hours end (0-23)
        is_24_hours: Whether resource operates 24 hours
    
    Returns:
        True if resource is available, False otherwise
    """
    # Convert UTC to EST for operating hours comparison
    est_tz = gettz('America/New_York')
    start_datetime_est = start_datetime_utc.astimezone(est_tz)
    end_datetime_est = end_datetime_utc.astimezone(est_tz)
    
    start_hour = start_datetime_est.hour
    start_minute = start_datetime_est.minute
    end_hour = end_datetime_est.hour
    end_minute = end_datetime_est.minute
    
    # Check operating hours (unless 24-hour operation)
    if not is_24_hours:
        # Start time must be at or after operating hours start
        # Match booking validation logic: start_hour must be >= operating_start
        # and if start_hour == operating_start, start_minute must be 0
        if start_hour < operating_hours_start or (start_hour == operating_hours_start and start_minute > 0):
            return False
        
        # End time must be at or before operating hours end
        # Match booking validation logic: end_hour must be <= operating_end
        # and if end_hour == operating_end, end_minute must be 0
        if end_hour > operating_hours_end or (end_hour == operating_hours_end and end_minute > 0):
            return False
    
    # Check for booking conflicts
    # Only check approved bookings
    cursor.execute("""
        SELECT COUNT(*) 
        FROM bookings 
        WHERE resource_id = ? 
        AND status = 'approved'
        AND start_datetime < ? AND end_datetime > ?
    """, (resource_id, end_datetime_utc.isoformat(), start_datetime_utc.isoformat()))
    
    conflict_count = cursor.fetchone()[0]
    return conflict_count == 0

