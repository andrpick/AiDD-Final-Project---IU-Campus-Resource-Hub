"""
Booking service with conflict detection.
"""
from datetime import datetime, timedelta
from src.data_access.database import get_db_connection
from dateutil.tz import tzutc
from dateutil import parser
from src.utils.logging_config import get_logger
from src.utils.exceptions import BookingError, ValidationError, ConflictError, NotFoundError
from src.utils.config import Config

logger = get_logger(__name__)

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

def validate_booking_datetime(start_datetime, end_datetime, resource_id=None):
    """Validate booking datetime constraints using resource-specific operating hours."""
    try:
        if isinstance(start_datetime, str):
            start_dt = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
        else:
            start_dt = start_datetime
        
        if isinstance(end_datetime, str):
            end_dt = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
        else:
            end_dt = end_datetime
    except (ValueError, TypeError) as e:
        logger.warning(f"Invalid datetime format: {e}")
        return False, None, None, "Invalid datetime format"
    
    # Ensure datetimes are timezone-aware (UTC)
    if start_dt.tzinfo is None:
        start_dt = start_dt.replace(tzinfo=tzutc())
    if end_dt.tzinfo is None:
        end_dt = end_dt.replace(tzinfo=tzutc())
    
    # Get current time in UTC for comparison
    now = datetime.now(tzutc())
    
    # Must be at least configured advance hours in the future
    min_advance = timedelta(hours=Config.BOOKING_MIN_ADVANCE_HOURS)
    if start_dt < now + min_advance:
        return False, None, None, f"Booking must be at least {Config.BOOKING_MIN_ADVANCE_HOURS} hour(s) in the future"
    
    # For operating hours validation, convert to configured timezone
    from dateutil.tz import gettz
    tz = gettz(Config.TIMEZONE)
    start_dt_local = start_dt.astimezone(tz)
    end_dt_local = end_dt.astimezone(tz)
    
    # Operating hours validation
    start_hour = start_dt_local.hour
    end_hour = end_dt_local.hour
    start_minute = start_dt_local.minute
    end_minute = end_dt_local.minute
    
    # End must be after start
    if end_dt <= start_dt:
        return False, None, None, "End datetime must be after start datetime"
    
    # Duration validation
    duration = end_dt - start_dt
    min_duration = timedelta(minutes=Config.BOOKING_MIN_DURATION_MINUTES)
    max_duration = timedelta(hours=Config.BOOKING_MAX_DURATION_HOURS)
    
    if duration < min_duration:
        return False, None, None, f"Minimum booking duration is {Config.BOOKING_MIN_DURATION_MINUTES} minutes"
    if duration > max_duration:
        return False, None, None, f"Maximum booking duration is {Config.BOOKING_MAX_DURATION_HOURS} hours"
    
    # Operating hours validation - fetch resource-specific hours
    if resource_id:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT operating_hours_start, operating_hours_end, is_24_hours
                FROM resources 
                WHERE resource_id = ?
            """, (resource_id,))
            result = cursor.fetchone()
            if result:
                operating_start = result['operating_hours_start']
                operating_end = result['operating_hours_end']
                is_24_hours = bool(result['is_24_hours']) if result['is_24_hours'] is not None else False
            else:
                return False, None, None, "Resource not found"
    else:
        # Fallback to global config if resource_id not provided (for backward compatibility)
        operating_start = Config.BOOKING_OPERATING_HOURS_START
        operating_end = Config.BOOKING_OPERATING_HOURS_END
        is_24_hours = False
    
    # Validate booking times are within operating hours (skip if 24-hour operation)
    if not is_24_hours:
        # Start time must be at or after operating_start
        if start_hour < operating_start or (start_hour == operating_start and start_minute > 0):
            return False, None, None, f"Booking must start at or after {operating_start:02d}:00"
        
        # End time must be at or before operating_end
        if end_hour > operating_end or (end_hour == operating_end and end_minute > 0):
            return False, None, None, f"Booking must end at or before {operating_end:02d}:00"
    
    return True, start_dt, end_dt, "Valid"

def create_booking(resource_id, requester_id, start_datetime, end_datetime, status='approved', request_reason=None):
    """
    Create a new booking request with transaction-level conflict checking.
    Uses a transaction to prevent race conditions where two users book the same slot simultaneously.
    
    Args:
        resource_id: ID of the resource
        requester_id: ID of the user requesting the booking
        start_datetime: Start datetime (ISO string or datetime object)
        end_datetime: End datetime (ISO string or datetime object)
        status: Booking status ('approved' for non-restricted, 'pending' for restricted)
        request_reason: Optional reason for booking request (for restricted resources)
    """
    # Validate datetime with resource-specific operating hours
    valid, start_dt, end_dt, msg = validate_booking_datetime(start_datetime, end_datetime, resource_id=resource_id)
    if not valid:
        return {'success': False, 'error': msg}
    
    # Use transaction with conflict check inside transaction to prevent race conditions
    # SQLite serializes writes, but we check conflicts within the transaction for safety
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Only check conflicts for approved bookings (pending bookings don't block other bookings)
        if status == 'approved':
            # Lock the row/s to prevent concurrent bookings (SQLite handles this, but explicit is better)
            # Re-check for conflicts within the transaction to prevent race conditions
            # This ensures that between check and insert, no other booking was created
            conflicts = check_conflicts(resource_id, start_dt, end_dt, cursor=cursor)
            if conflicts:
                logger.warning(f"Booking conflict detected for resource {resource_id}: {len(conflicts)} conflicts")
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
        
        # Insert booking with specified status
        cursor.execute("""
            INSERT INTO bookings (resource_id, requester_id, start_datetime, end_datetime, status, rejection_reason)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (resource_id, requester_id, start_dt.isoformat(), end_dt.isoformat(), status, request_reason))
        
        booking_id = cursor.lastrowid
        conn.commit()
        logger.info(f"Created booking {booking_id} for resource {resource_id} by user {requester_id} with status {status}")
    
    # Send notification for booking creation
    try:
        from src.services.notification_service import send_booking_confirmation
        from src.models.user import User
        from src.services.resource_service import get_resource
        
        user = User.get(requester_id)
        resource_result = get_resource(resource_id)
        
        if user and resource_result['success']:
            resource = resource_result['data']
            requester_email = user.email if user.email else 'unknown@example.com'
            send_booking_confirmation(
                booking_id=booking_id,
                requester_email=requester_email,
                resource_title=resource.get('title', 'Unknown Resource'),
                start_datetime=start_dt,
                end_datetime=end_dt
            )
    except Exception as e:
        logger.warning(f"Failed to send booking confirmation notification: {e}")
    
    return {'success': True, 'data': {'booking_id': booking_id}}

def mark_completed_bookings():
    """
    Automatically mark approved bookings as completed when their end_datetime has passed.
    This function should be called periodically or when bookings are accessed.
    """
    now = datetime.now(tzutc())
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Find all approved bookings where end_datetime < current_time
        cursor.execute("""
            SELECT booking_id, end_datetime
            FROM bookings
            WHERE status = 'approved'
            AND end_datetime < ?
        """, (now.isoformat(),))
        
        bookings_to_complete = cursor.fetchall()
        
        if bookings_to_complete:
            # Update all found bookings to completed status
            booking_ids = [row['booking_id'] for row in bookings_to_complete]
            placeholders = ','.join(['?'] * len(booking_ids))
            
            cursor.execute(f"""
                UPDATE bookings
                SET status = 'completed', updated_at = CURRENT_TIMESTAMP
                WHERE booking_id IN ({placeholders})
            """, booking_ids)
            
            conn.commit()
            
            return {'success': True, 'data': {'count': len(booking_ids)}}
    
    return {'success': True, 'data': {'count': 0}}

def get_booking(booking_id):
    """Get a booking by ID. Automatically marks as completed if past end time."""
    # Mark completed bookings before getting specific booking
    mark_completed_bookings()
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,))
        row = cursor.fetchone()
        
        if row:
            return {'success': True, 'data': dict(row)}
        logger.warning(f"Booking {booking_id} not found")
        return {'success': False, 'error': 'Booking not found'}

def update_booking_status(booking_id, status, rejection_reason=None):
    """Update booking status. Valid statuses: approved, cancelled, completed, pending, denied."""
    if status not in ['approved', 'cancelled', 'completed', 'pending', 'denied']:
        logger.warning(f"Invalid booking status attempted: {status}")
        return {'success': False, 'error': 'Invalid status'}
    
    # Get existing booking to get old status and requester info
    booking_result = get_booking(booking_id)
    if not booking_result['success']:
        return {'success': False, 'error': 'Booking not found'}
    
    existing_booking = booking_result['data']
    old_status = existing_booking.get('status')
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Set rejection_reason if provided and status is denied
        if status == 'denied' and rejection_reason:
            cursor.execute("""
                UPDATE bookings
                SET status = ?, rejection_reason = ?, updated_at = CURRENT_TIMESTAMP
                WHERE booking_id = ?
            """, (status, rejection_reason, booking_id))
        else:
            cursor.execute("""
                UPDATE bookings
                SET status = ?, rejection_reason = NULL, updated_at = CURRENT_TIMESTAMP
                WHERE booking_id = ?
            """, (status, booking_id))
        
        if cursor.rowcount == 0:
            logger.warning(f"Booking {booking_id} not found for status update")
            return {'success': False, 'error': 'Booking not found'}
        
        logger.info(f"Updated booking {booking_id} status from {old_status} to {status}")
    
    # Send notification for status change
    try:
        from src.services.notification_service import send_booking_status_change
        from src.models.user import User
        from src.services.resource_service import get_resource
        
        requester_id = existing_booking.get('requester_id')
        resource_id = existing_booking.get('resource_id')
        user = User.get(requester_id) if requester_id else None
        resource_result = get_resource(resource_id) if resource_id else {'success': False}
        
        if user and resource_result['success']:
            resource = resource_result['data']
            requester_email = user.email if user.email else 'unknown@example.com'
            send_booking_status_change(
                booking_id=booking_id,
                requester_email=requester_email,
                resource_title=resource.get('title', 'Unknown Resource'),
                old_status=old_status,
                new_status=status,
                reason=rejection_reason
            )
    except Exception as e:
        logger.warning(f"Failed to send booking status change notification: {e}")
    
    return {'success': True, 'data': {'booking_id': booking_id}}

def update_booking(booking_id, start_datetime=None, end_datetime=None, status=None, rejection_reason=None, skip_validation=False):
    """Update booking fields. Admin can overwrite bookings."""
    # Get existing booking
    booking_result = get_booking(booking_id)
    if not booking_result['success']:
        return {'success': False, 'error': 'Booking not found'}
    
    existing_booking = booking_result['data']
    resource_id = existing_booking['resource_id']
    
    # Use existing values if not provided
    new_start = start_datetime if start_datetime is not None else existing_booking['start_datetime']
    new_end = end_datetime if end_datetime is not None else existing_booking['end_datetime']
    new_status = status if status is not None else existing_booking['status']
    
    # Validate datetime if provided and validation not skipped
    if not skip_validation and (start_datetime is not None or end_datetime is not None):
        valid, start_dt, end_dt, msg = validate_booking_datetime(new_start, new_end, resource_id=resource_id)
        if not valid:
            return {'success': False, 'error': msg}
        new_start = start_dt.isoformat()
        new_end = end_dt.isoformat()
    
    # Validate status
    if new_status not in ['approved', 'cancelled', 'completed', 'pending', 'denied']:
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
    """List bookings with filters. Automatically marks completed bookings."""
    # Mark completed bookings before listing
    mark_completed_bookings()
    
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

