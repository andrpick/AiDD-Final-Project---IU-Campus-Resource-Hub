"""
Review and rating service.
"""
from datetime import datetime, timedelta
from dateutil.tz import tzutc
from src.data_access.database import get_db_connection

def create_review(resource_id, reviewer_id, rating, comment=None, booking_id=None):
    """Create a review for a resource.
    
    Users can review a resource as many times as they have completed bookings for it.
    Each review can optionally be linked to a specific booking_id.
    """
    # Validate rating
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return {'success': False, 'error': 'Rating must be between 1 and 5'}
    
    # Validate comment
    if comment:
        if len(comment) > 2000:
            return {'success': False, 'error': 'Comment must be less than 2000 characters'}
        # Don't escape here - Jinja2 will handle escaping on output
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Count completed bookings for this user and resource
        # A booking is considered completed if:
        # 1. Status is 'completed', OR
        # 2. Status is 'approved' AND end_datetime has passed
        now = datetime.now(tzutc())
        cursor.execute("""
            SELECT COUNT(*) as completed_count
            FROM bookings
            WHERE resource_id = ?
            AND requester_id = ?
            AND (
                status = 'completed'
                OR (status = 'approved' AND end_datetime < ?)
            )
        """, (resource_id, reviewer_id, now.isoformat()))
        
        completed_bookings = cursor.fetchone()['completed_count']
        
        if completed_bookings == 0:
            return {'success': False, 'error': 'You must have at least one completed booking for this resource to leave a review'}
        
        # Count existing reviews for this user and resource
        cursor.execute("""
            SELECT COUNT(*) as review_count
            FROM reviews
            WHERE resource_id = ? AND reviewer_id = ?
        """, (resource_id, reviewer_id))
        
        existing_reviews = cursor.fetchone()['review_count']
        
        # Check if user has exceeded their review limit
        if existing_reviews >= completed_bookings:
            return {
                'success': False, 
                'error': f'You can only leave {completed_bookings} review(s) for this resource (one per completed booking). You have already left {existing_reviews} review(s).'
            }
        
        # If booking_id is provided, validate it
        if booking_id:
            cursor.execute("""
                SELECT * FROM bookings
                WHERE booking_id = ? AND requester_id = ? AND resource_id = ?
            """, (booking_id, reviewer_id, resource_id))
            booking = cursor.fetchone()
            
            if not booking:
                return {'success': False, 'error': 'Invalid booking'}
            
            booking_dict = dict(booking)
            
            # Check if booking is completed (status='completed' or past end time)
            is_completed = False
            if booking_dict['status'] == 'completed':
                is_completed = True
            else:
                end_dt = datetime.fromisoformat(booking_dict['end_datetime'].replace('Z', '+00:00'))
                if end_dt < now:
                    is_completed = True
            
            if not is_completed:
                return {'success': False, 'error': 'Can only review completed bookings'}
            
            # Check if this booking has already been reviewed
            cursor.execute("""
                SELECT COUNT(*) as review_count
                FROM reviews
                WHERE booking_id = ? AND reviewer_id = ?
            """, (booking_id, reviewer_id))
            
            booking_review_count = cursor.fetchone()['review_count']
            if booking_review_count > 0:
                return {'success': False, 'error': 'This booking has already been reviewed'}
        
        # Insert review
        cursor.execute("""
            INSERT INTO reviews (resource_id, reviewer_id, booking_id, rating, comment)
            VALUES (?, ?, ?, ?, ?)
        """, (resource_id, reviewer_id, booking_id, rating, comment))
        
        review_id = cursor.lastrowid
    
    return {'success': True, 'data': {'review_id': review_id}}

def update_review(review_id, reviewer_id, rating=None, comment=None):
    """Update a review (within 30 days of creation)."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM reviews WHERE review_id = ?", (review_id,))
        review = cursor.fetchone()
        
        if not review:
            return {'success': False, 'error': 'Review not found'}
        
        review_dict = dict(review)
        
        # Check ownership
        if review_dict['reviewer_id'] != reviewer_id:
            return {'success': False, 'error': 'Unauthorized'}
        
        # Check 30-day window
        created_at = datetime.fromisoformat(review_dict['timestamp'].replace('Z', '+00:00'))
        if datetime.now() - created_at > timedelta(days=30):
            return {'success': False, 'error': 'Review can only be updated within 30 days'}
        
        # Validate updates
        updates = []
        values = []
        
        if rating is not None:
            if not isinstance(rating, int) or rating < 1 or rating > 5:
                return {'success': False, 'error': 'Rating must be between 1 and 5'}
            updates.append("rating = ?")
            values.append(rating)
        
        if comment is not None:
            if len(comment) > 2000:
                return {'success': False, 'error': 'Comment must be less than 2000 characters'}
            # Don't escape here - Jinja2 will handle escaping on output
            updates.append("comment = ?")
            values.append(comment)
        
        if not updates:
            return {'success': False, 'error': 'No fields to update'}
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        values.append(review_id)
        
        cursor.execute(f"""
            UPDATE reviews
            SET {', '.join(updates)}
            WHERE review_id = ?
        """, values)
    
    return {'success': True, 'data': {'review_id': review_id}}

def delete_review(review_id, user_id, is_admin=False):
    """Delete a review."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT reviewer_id FROM reviews WHERE review_id = ?", (review_id,))
        review = cursor.fetchone()
        
        if not review:
            return {'success': False, 'error': 'Review not found'}
        
        if not is_admin and dict(review)['reviewer_id'] != user_id:
            return {'success': False, 'error': 'Unauthorized'}
        
        cursor.execute("DELETE FROM reviews WHERE review_id = ?", (review_id,))
    
    return {'success': True, 'data': {'review_id': review_id}}

def get_resource_reviews(resource_id, limit=20, offset=0):
    """Get reviews for a resource."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT r.*, COALESCE(u.name, '[Deleted User]') as reviewer_name
            FROM reviews r
            LEFT JOIN users u ON r.reviewer_id = u.user_id AND (u.deleted = 0 OR u.deleted IS NULL)
            WHERE r.resource_id = ?
            ORDER BY r.timestamp DESC
            LIMIT ? OFFSET ?
        """, (resource_id, limit, offset))
        
        reviews = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute("SELECT COUNT(*) FROM reviews WHERE resource_id = ?", (resource_id,))
        total = cursor.fetchone()[0]
        
        # Get aggregate stats
        cursor.execute("""
            SELECT 
                AVG(rating) as avg_rating,
                COUNT(*) as total_reviews,
                SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END) as rating_5,
                SUM(CASE WHEN rating = 4 THEN 1 ELSE 0 END) as rating_4,
                SUM(CASE WHEN rating = 3 THEN 1 ELSE 0 END) as rating_3,
                SUM(CASE WHEN rating = 2 THEN 1 ELSE 0 END) as rating_2,
                SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as rating_1
            FROM reviews
            WHERE resource_id = ?
        """, (resource_id,))
        
        stats = cursor.fetchone()
        stats_dict = dict(stats) if stats else {}
    
    return {
        'success': True,
        'data': {
            'reviews': reviews,
            'total': total,
            'stats': {
                'avg_rating': float(stats_dict.get('avg_rating', 0)) if stats_dict.get('avg_rating') else None,
                'total_reviews': stats_dict.get('total_reviews', 0),
                'rating_distribution': {
                    5: stats_dict.get('rating_5', 0),
                    4: stats_dict.get('rating_4', 0),
                    3: stats_dict.get('rating_3', 0),
                    2: stats_dict.get('rating_2', 0),
                    1: stats_dict.get('rating_1', 0)
                }
            }
        }
    }

