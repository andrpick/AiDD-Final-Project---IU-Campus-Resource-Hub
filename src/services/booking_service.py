"""
Booking service with conflict detection.
"""
from datetime import datetime, timedelta
from src.data_access.database import get_db_connection

def check_conflicts(resource_id, start_datetime, end_datetime, exclude_booking_id=None, cursor=None):
    """
    Check for conflicting bookings.
    Two bookings conflict if their time ranges overlap.
    Overlap occurs when: (start_datetime < new_end_datetime AND end_datetime > new_start_datetime)
    
    Args:
        resource_id: ID of the resource
        start_datetime: Start datetime (datetime object or ISO string)
        end_datetime: End datetime (datetime object or ISO string)
        exclude_booking_id: Optional booking ID to exclude from conflict check
        cursor: Optional database cursor to use (for transaction safety)
    
    Returns:
        List of conflicting bookings
    """
    # Convert to datetime objects if strings
    if isinstance(start_datetime, str):
        start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
    else:
        start_dt = start_datetime
        
    if isinstance(end_datetime, str):
        end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
    else:
        end_dt = end_datetime
    
    # Standard overlap check: (existing_start < new_end AND existing_end > new_start)
    # Only check approved bookings since bookings are auto-approved on creation
    query = """
        SELECT * FROM bookings
        WHERE resource_id = ?
        AND status = 'approved'
        AND start_datetime < ? AND end_datetime > ?
    """
    params = [resource_id, end_dt.isoformat(), start_dt.isoformat()]
    
    if exclude_booking_id:
        query += " AND booking_id != ?"
        params.append(exclude_booking_id)
    
    if cursor:
        # Use provided cursor (for transaction safety)
        cursor.execute(query, params)
        conflicts = [dict(row) for row in cursor.fetchall()]
    else:
        # Create new connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conflicts = [dict(row) for row in cursor.fetchall()]
    
    return conflicts

def validate_booking_datetime(start_datetime, end_datetime):
    """Validate booking datetime constraints."""
    from dateutil.tz import tzutc
    try:
        if isinstance(start_datetime, str):
            start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
        else:
            start_dt = start_datetime
        
        if isinstance(end_datetime, str):
            end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
        else:
            end_dt = end_datetime
    except Exception:
        return False, None, None, "Invalid datetime format"
    
    # Ensure datetimes are timezone-aware (UTC)
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=tzutc())
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=tzutc())
    
    # Get current time in UTC for comparison
    now = datetime.now(tzutc())
    
    # Must be at least 1 hour in the future
    if start_dt < now + timedelta(hours=1):
        return False, None, None, "Booking must be at least 1 hour in the future"
    
    # For operating hours validation, convert to EST/EDT
    from dateutil.tz import gettz
    est_tz = gettz('America/New_York')
    start_dt_est = start_dt.astimezone(est_tz)
    end_dt_est = end_dt.astimezone(est_tz)
    
    # Operating hours: 8 AM - 10 PM (EST/EDT)
    start_hour = start_dt_est.hour
    end_hour = end_dt_est.hour
    
    # End must be after start
    if end_dt <= start_dt:
        return False, None, None, "End datetime must be after start datetime"
    
    # Duration must be between 30 minutes and 8 hours
    duration = end_dt - start_dt
    if duration < timedelta(minutes=30):
        return False, None, None, "Minimum booking duration is 30 minutes"
    if duration > timedelta(hours=8):
        return False, None, None, "Maximum booking duration is 8 hours"
    
    # Operating hours: 8 AM - 10 PM (EST/EDT)
    if start_hour < 8:
        return False, None, None, "Booking must start at or after 8:00 AM"
    if start_hour == 8 and start_dt_est.minute > 0:
        return False, None, None, "Booking must start at or after 8:00 AM"
    
    if end_hour > 22:
        return False, None, None, "Booking must end at or before 10:00 PM"
    if end_hour == 22 and end_dt_est.minute > 0:
        return False, None, None, "Booking must end at or before 10:00 PM"
    
    return True, start_dt, end_dt, "Valid"

def create_booking(resource_id, requester_id, start_datetime, end_datetime):
    """
    Create a new booking request with transaction-level conflict checking.
    Uses a transaction to prevent race conditions where two users book the same slot simultaneously.
    """
    # Validate datetime
    valid, start_dt, end_dt, msg = validate_booking_datetime(start_datetime, end_datetime)
    if not valid:
        return {'success': False, 'error': msg}
    
    # Use transaction with conflict check inside transaction to prevent race conditions
    # SQLite serializes writes, but we check conflicts within the transaction for safety
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Lock the row/s to prevent concurrent bookings (SQLite handles this, but explicit is better)
        # Re-check for conflicts within the transaction to prevent race conditions
        # This ensures that between check and insert, no other booking was created
        conflicts = check_conflicts(resource_id, start_dt, end_dt, cursor=cursor)
        if conflicts:
            conn.rollback()
            conflict_details = []
            for conflict in conflicts:
                conflict_details.append({
                    'booking_id': conflict.get('booking_id'),
                    'start': conflict.get('start_datetime'),
                    'end': conflict.get('end_datetime'),
                    'status': conflict.get('status')
                })
            return {
                'success': False,
                'error': 'Time slot conflicts with existing booking',
                'conflicts': conflicts
            }
        
        # If no conflicts, automatically approve the booking
        status = 'approved'
        
        # Insert booking with auto-approval within the same transaction
        cursor.execute("""
            INSERT INTO bookings (resource_id, requester_id, start_datetime, end_datetime, status)
            VALUES (?, ?, ?, ?, ?)
        """, (resource_id, requester_id, start_dt.isoformat(), end_dt.isoformat(), status))
        
        booking_id = cursor.lastrowid
        conn.commit()
    
    return {'success': True, 'data': {'booking_id': booking_id}}

def get_booking(booking_id):
    """Get a booking by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
        row = cursor.fetchone()
        
        if row:
            return {'success': True, 'data': dict(row)}
        return {'success': False, 'error': 'Booking not found'}

def update_booking_status(booking_id, status, rejection_reason=None):
    """Update booking status. Valid statuses: approved, cancelled, completed."""
    if status not in ['approved', 'cancelled', 'completed']:
        return {'success': False, 'error': 'Invalid status'}
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE bookings
            SET status = ?, rejection_reason = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE booking_id = ?
        """, (status, booking_id))
        
        if cursor.rowcount == 0:
            return {'success': False, 'error': 'Booking not found'}
    
    return {'success': True, 'data': {'booking_id': booking_id}}

def update_booking(booking_id, start_datetime=None, end_datetime=None, status=None, rejection_reason=None, skip_validation=False):
    """Update booking fields. Admin can overwrite bookings."""
    # Get existing booking
    booking_result = get_booking(booking_id)
    if not booking_result['success']:
        return {'success': False, 'error': 'Booking not found'}
    
    existing_booking = booking_result['data']
    
    # Use existing values if not provided
    new_start = start_datetime if start_datetime is not None else existing_booking['start_datetime']
    new_end = end_datetime if end_datetime is not None else existing_booking['end_datetime']
    new_status = status if status is not None else existing_booking['status']
    
    # Validate datetime if provided and validation not skipped
    if not skip_validation and (start_datetime is not None or end_datetime is not None):
        valid, start_dt, end_dt, msg = validate_booking_datetime(new_start, new_end)
        if not valid:
            return {'success': False, 'error': msg}
        new_start = start_dt.isoformat()
        new_end = end_dt.isoformat()
    
    # Validate status
    if new_status not in ['approved', 'cancelled', 'completed']:
        return {'success': False, 'error': 'Invalid status'}
    
    # Update booking
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE bookings
            SET start_datetime = ?, end_datetime = ?, status = ?, 
                rejection_reason = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE booking_id = ?
        """, (new_start, new_end, new_status, booking_id))
        
        if cursor.rowcount == 0:
            return {'success': False, 'error': 'Booking not found'}
    
    return {'success': True, 'data': {'booking_id': booking_id}}

def list_bookings(user_id=None, resource_id=None, status=None, limit=20, offset=0):
    """List bookings with filters."""
    conditions = []
    values = []
    
    if user_id:
        conditions.append("requester_id = ?")
        values.append(user_id)
    
    if resource_id:
        conditions.append("resource_id = ?")
        values.append(resource_id)
    
    if status:
        conditions.append("status = ?")
        values.append(status)
    
    where_clause = " AND ".join(conditions) if conditions else "1=1"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT * FROM bookings
            WHERE {where_clause}
            ORDER BY start_datetime DESC
            LIMIT ? OFFSET ?
        """, values + [limit, offset])
        
        bookings = [dict(row) for row in cursor.fetchall()]
        
        cursor.execute(f"SELECT COUNT(*) FROM bookings WHERE {where_clause}", values)
        total = cursor.fetchone()[0]
    
    return {'success': True, 'data': {'bookings': bookings, 'total': total}}

