"""
Bookings controller (Flask blueprint).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, Response
from flask_login import login_required, current_user
from src.services.booking_service import create_booking, get_booking, update_booking_status, list_bookings, check_conflicts
from src.services.resource_service import get_resource
from datetime import datetime
import urllib.parse

bookings_bp = Blueprint('bookings', __name__, url_prefix='/bookings')

@bookings_bp.route('/')
@login_required
def index():
    """List user's bookings."""
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    page_size = min(100, max(1, request.args.get('page_size', 20, type=int)))
    offset = (page - 1) * page_size
    
    result = list_bookings(user_id=current_user.user_id, status=status, limit=page_size, offset=offset)
    
    if result['success']:
        bookings = result['data']['bookings']
        total = result['data']['total']
        total_pages = (total + page_size - 1) // page_size
        
        # Enrich with resource info
        for booking in bookings:
            resource_result = get_resource(booking['resource_id'])
            if resource_result['success']:
                booking['resource'] = resource_result['data']
        
        return render_template('bookings/index.html',
                             bookings=bookings,
                             page=page,
                             total_pages=total_pages,
                             total=total,
                             status_filter=status)
    else:
        return render_template('bookings/index.html', bookings=[], page=1, total_pages=0, total=0)

@bookings_bp.route('/create', methods=['POST'])
@login_required
def create():
    """Create a booking request."""
    from dateutil.tz import gettz, tzutc
    
    resource_id = request.form.get('resource_id', type=int)
    start_datetime_str = request.form.get('start_datetime', '').strip()
    end_datetime_str = request.form.get('end_datetime', '').strip()
    
    if not resource_id or not start_datetime_str or not end_datetime_str:
        flash('Missing required fields.', 'error')
        return redirect(request.referrer or url_for('search.index'))
    
    # Convert datetime-local input (EST/EDT) to UTC for storage
    try:
        # Parse as local time (EST/EDT)
        est_tz = gettz('America/New_York')
        start_dt_local = datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M')
        start_dt_local = start_dt_local.replace(tzinfo=est_tz)
        # Convert to UTC
        start_dt_utc = start_dt_local.astimezone(tzutc())
        start_datetime = start_dt_utc.isoformat()
        
        end_dt_local = datetime.strptime(end_datetime_str, '%Y-%m-%dT%H:%M')
        end_dt_local = end_dt_local.replace(tzinfo=est_tz)
        # Convert to UTC
        end_dt_utc = end_dt_local.astimezone(tzutc())
        end_datetime = end_dt_utc.isoformat()
    except Exception as e:
        flash(f'Invalid datetime format: {str(e)}', 'error')
        return redirect(request.referrer or url_for('search.index'))
    
    # Verify resource exists and is published
    resource_result = get_resource(resource_id)
    if not resource_result['success']:
        flash('Resource not found.', 'error')
        return redirect(url_for('search.index'))
    
    resource = resource_result['data']
    if resource['status'] != 'published':
        flash('Resource is not available for booking.', 'error')
        return redirect(url_for('resources.detail', resource_id=resource_id))
    
    result = create_booking(resource_id, current_user.user_id, start_datetime, end_datetime)
    
    if result['success']:
        # Check if booking was auto-approved (status will be 'approved')
        from src.services.booking_service import get_booking
        booking_result = get_booking(result['data']['booking_id'])
        if booking_result['success'] and booking_result['data']['status'] == 'approved':
            flash('Booking approved automatically! The time slot is confirmed.', 'success')
        else:
            flash('Booking request submitted successfully.', 'success')
        return redirect(url_for('bookings.detail', booking_id=result['data']['booking_id']))
    else:
        flash(result['error'], 'error')
        return redirect(url_for('resources.detail', resource_id=resource_id))

@bookings_bp.route('/<int:booking_id>')
@login_required
def detail(booking_id):
    """View booking details."""
    result = get_booking(booking_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('bookings.index'))
    
    booking = result['data']
    
    # Permission check
    if booking['requester_id'] != current_user.user_id:
        # Check if user is owner/staff/admin
        resource_result = get_resource(booking['resource_id'])
        if not resource_result['success']:
            flash('Unauthorized.', 'error')
            return redirect(url_for('bookings.index'))
        
        resource = resource_result['data']
        if resource['owner_id'] != current_user.user_id and not current_user.is_staff():
            flash('Unauthorized.', 'error')
            return redirect(url_for('bookings.index'))
    
    # Get resource info
    resource_result = get_resource(booking['resource_id'])
    resource = resource_result['data'] if resource_result['success'] else None
    
    return render_template('bookings/detail.html', booking=booking, resource=resource)

@bookings_bp.route('/<int:booking_id>/approve', methods=['POST'])
@login_required
def approve(booking_id):
    """Approve a booking."""
    result = get_booking(booking_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('bookings.index'))
    
    booking = result['data']
    
    # Permission check
    resource_result = get_resource(booking['resource_id'])
    if not resource_result['success']:
        flash('Resource not found.', 'error')
        return redirect(url_for('bookings.index'))
    
    resource = resource_result['data']
    
    if resource['owner_id'] != current_user.user_id and not current_user.is_staff():
        flash('Unauthorized.', 'error')
        return redirect(url_for('bookings.detail', booking_id=booking_id))
    
    if booking['status'] != 'pending':
        flash('Only pending bookings can be approved.', 'error')
        return redirect(url_for('bookings.detail', booking_id=booking_id))
    
    # Re-check conflicts
    conflicts = check_conflicts(booking['resource_id'], booking['start_datetime'], booking['end_datetime'], booking_id)
    if conflicts:
        flash('Booking conflicts with existing bookings. Please review.', 'error')
        return redirect(url_for('bookings.detail', booking_id=booking_id))
    
    result = update_booking_status(booking_id, 'approved')
    
    if result['success']:
        flash('Booking approved successfully.', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('bookings.detail', booking_id=booking_id))

@bookings_bp.route('/<int:booking_id>/reject', methods=['POST'])
@login_required
def reject(booking_id):
    """Reject a booking."""
    result = get_booking(booking_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('bookings.index'))
    
    booking = result['data']
    
    # Permission check
    resource_result = get_resource(booking['resource_id'])
    if not resource_result['success']:
        flash('Resource not found.', 'error')
        return redirect(url_for('bookings.index'))
    
    resource = resource_result['data']
    
    if resource['owner_id'] != current_user.user_id and not current_user.is_staff():
        flash('Unauthorized.', 'error')
        return redirect(url_for('bookings.detail', booking_id=booking_id))
    
    if booking['status'] != 'pending':
        flash('Only pending bookings can be rejected.', 'error')
        return redirect(url_for('bookings.detail', booking_id=booking_id))
    
    rejection_reason = request.form.get('rejection_reason', '').strip()
    if not rejection_reason:
        flash('Rejection reason is required.', 'error')
        return redirect(url_for('bookings.detail', booking_id=booking_id))
    
    result = update_booking_status(booking_id, 'rejected', rejection_reason)
    
    if result['success']:
        flash('Booking rejected.', 'info')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('bookings.detail', booking_id=booking_id))

@bookings_bp.route('/<int:booking_id>/cancel', methods=['POST'])
@login_required
def cancel(booking_id):
    """Cancel a booking."""
    result = get_booking(booking_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('bookings.index'))
    
    booking = result['data']
    
    # Permission check
    if booking['requester_id'] != current_user.user_id and not current_user.is_admin():
        flash('Unauthorized.', 'error')
        return redirect(url_for('bookings.detail', booking_id=booking_id))
    
    if booking['status'] not in ['pending', 'approved']:
        flash('Only pending or approved bookings can be cancelled.', 'error')
        return redirect(url_for('bookings.detail', booking_id=booking_id))
    
    result = update_booking_status(booking_id, 'cancelled')
    
    if result['success']:
        flash('Booking cancelled.', 'info')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('bookings.detail', booking_id=booking_id))

@bookings_bp.route('/check-conflicts', methods=['POST'])
@login_required
def check_conflicts_endpoint():
    """Check for booking conflicts."""
    # This would be used by AJAX to check conflicts before submission
    data = request.get_json()
    resource_id = data.get('resource_id')
    start_datetime = data.get('start_datetime')
    end_datetime = data.get('end_datetime')
    
    if not all([resource_id, start_datetime, end_datetime]):
        return {'success': False, 'error': 'Missing required fields'}, 400
    
    conflicts = check_conflicts(resource_id, start_datetime, end_datetime)
    
    return {
        'success': True,
        'has_conflicts': len(conflicts) > 0,
        'conflicts': conflicts
    }

@bookings_bp.route('/<int:booking_id>/calendar/<calendar_type>')
@login_required
def export_calendar(booking_id, calendar_type):
    """Export booking to calendar (Google Calendar, Outlook, iCal)."""
    result = get_booking(booking_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('bookings.index'))
    
    booking = result['data']
    
    # Permission check - only requester can export
    if booking['requester_id'] != current_user.user_id:
        flash('Unauthorized.', 'error')
        return redirect(url_for('bookings.detail', booking_id=booking_id))
    
    # Get resource info
    resource_result = get_resource(booking['resource_id'])
    resource = resource_result['data'] if resource_result['success'] else None
    
    # Parse datetimes
    start_dt = datetime.fromisoformat(booking['start_datetime'].replace('Z', '+00:00'))
    end_dt = datetime.fromisoformat(booking['end_datetime'].replace('Z', '+00:00'))
    
    # Format for calendar
    resource_title = resource.get('title', f'Resource #{booking["resource_id"]}') if resource else f'Resource #{booking["resource_id"]}'
    location = resource.get('location', '') if resource else ''
    description = resource.get('description', '') if resource else ''
    
    # Generate calendar URL based on type
    if calendar_type == 'google':
        # Google Calendar URL format
        start_str = start_dt.strftime('%Y%m%dT%H%M%S')
        end_str = end_dt.strftime('%Y%m%dT%H%M%S')
        title = urllib.parse.quote(f'Booking: {resource_title}')
        details = urllib.parse.quote(f'Resource booking at {location}\n\n{description}')
        location_encoded = urllib.parse.quote(location)
        
        url = f'https://calendar.google.com/calendar/render?action=TEMPLATE&text={title}&dates={start_str}/{end_str}&details={details}&location={location_encoded}'
        return redirect(url)
        
    elif calendar_type == 'outlook':
        # Outlook Calendar URL format
        start_str = start_dt.isoformat().replace('+00:00', 'Z')
        end_str = end_dt.isoformat().replace('+00:00', 'Z')
        title = urllib.parse.quote(f'Booking: {resource_title}')
        body = urllib.parse.quote(f'Resource booking at {location}\n\n{description}')
        location_encoded = urllib.parse.quote(location)
        
        url = f'https://outlook.live.com/calendar/0/deeplink/compose?subject={title}&startdt={start_str}&enddt={end_str}&body={body}&location={location_encoded}'
        return redirect(url)
        
    elif calendar_type == 'ical':
        # iCal file format
        from datetime import timezone as tz
        
        def format_datetime_ical(dt):
            """Format datetime in iCal format (UTC)."""
            # Ensure datetime has timezone info
            if dt.tzinfo is None:
                # Assume UTC if no timezone
                dt = dt.replace(tzinfo=tz.utc)
            else:
                # Convert to UTC
                dt = dt.astimezone(tz.utc)
            # Format as UTC string
            return dt.strftime('%Y%m%dT%H%M%SZ')
        
        start_ical = format_datetime_ical(start_dt)
        end_ical = format_datetime_ical(end_dt)
        now_ical = format_datetime_ical(datetime.now(tz.utc))
        
        # Escape description for iCal
        ical_description = description.replace('\n', '\\n').replace('\r', '')
        ical_location = location.replace('\n', ' ').replace('\r', '')
        
        # Generate iCal content (must use CRLF line endings)
        ical_content = f"""BEGIN:VCALENDAR\r
VERSION:2.0\r
PRODID:-//Indiana University Campus Resource Hub//Booking Calendar//EN\r
CALSCALE:GREGORIAN\r
METHOD:PUBLISH\r
BEGIN:VEVENT\r
UID:booking-{booking_id}@campus-resource-hub\r
DTSTAMP:{now_ical}\r
DTSTART:{start_ical}\r
DTEND:{end_ical}\r
SUMMARY:Booking: {resource_title}\r
DESCRIPTION:Resource booking at {ical_location}\\n\\n{ical_description}\r
LOCATION:{ical_location}\r
STATUS:CONFIRMED\r
SEQUENCE:0\r
END:VEVENT\r
END:VCALENDAR"""
        
        # Return as downloadable file
        response = Response(ical_content, mimetype='text/calendar; charset=utf-8')
        response.headers['Content-Disposition'] = f'attachment; filename="booking-{booking_id}.ics"'
        return response
    
    else:
        flash('Invalid calendar type.', 'error')
        return redirect(url_for('bookings.detail', booking_id=booking_id))

