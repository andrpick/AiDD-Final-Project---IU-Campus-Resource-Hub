"""
Calendar processing utilities for resource booking views.
"""
from datetime import datetime, timedelta, date, time as dt_time
from calendar import monthrange, monthcalendar
from dateutil.tz import gettz, tzutc
from src.utils.datetime_utils import parse_datetime_aware, convert_to_est
from src.utils.logging_config import get_logger
from src.utils.config import Config
from src.data_access.database import get_db_connection

logger = get_logger(__name__)


def prepare_calendar_data(resource_id, approved_bookings_raw, selected_year, selected_month, selected_day=None):
    """
    Prepare calendar data for resource detail view.
    
    Args:
        resource_id: ID of the resource
        approved_bookings_raw: List of booking dictionaries from database
        selected_year: Year to display
        selected_month: Month to display
        selected_day: Optional day to display (for day view)
    
    Returns:
        Dictionary with calendar_data, day_data, booked_slots, and navigation info
    """
    # Fetch resource-specific operating hours
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT operating_hours_start, operating_hours_end, is_24_hours
            FROM resources 
            WHERE resource_id = ?
        """, (resource_id,))
        result = cursor.fetchone()
        if result:
            operating_hours_start = result['operating_hours_start']
            operating_hours_end = result['operating_hours_end']
            is_24_hours = bool(result['is_24_hours']) if result['is_24_hours'] is not None else False
            if is_24_hours:
                # For 24-hour operation, show all hours
                operating_hours_start = 0
                operating_hours_end = 23
        else:
            # Fallback to global config if resource not found
            logger.warning(f"Resource {resource_id} not found, using global operating hours")
            operating_hours_start = Config.BOOKING_OPERATING_HOURS_START
            operating_hours_end = Config.BOOKING_OPERATING_HOURS_END
            is_24_hours = False
    
    now = datetime.now()
    today = now.date()
    
    # Validate month/year (cannot go before current month)
    if selected_year < today.year or (selected_year == today.year and selected_month < today.month):
        selected_year = today.year
        selected_month = today.month
    
    # Calculate month boundaries
    month_start = date(selected_year, selected_month, 1)
    days_in_month = monthrange(selected_year, selected_month)[1]
    month_end = date(selected_year, selected_month, days_in_month)
    
    # Generate calendar grid for the month (6 weeks x 7 days)
    month_calendar = monthcalendar(selected_year, selected_month)
    
    # Calculate previous and next month
    if selected_month == 1:
        prev_year = selected_year - 1
        prev_month = 12
        next_year = selected_year
        next_month = 2
    elif selected_month == 12:
        prev_year = selected_year
        prev_month = 11
        next_year = selected_year + 1
        next_month = 1
    else:
        prev_year = selected_year
        prev_month = selected_month - 1
        next_year = selected_year
        next_month = selected_month + 1
    
    # Check if we can navigate to previous month
    can_go_prev = not (prev_year < today.year or (prev_year == today.year and prev_month < today.month))
    
    # Calculate current time position for today's indicator (only in month view)
    current_time_info = None
    if selected_year == today.year and selected_month == today.month and not selected_day:
        current_hour = now.hour
        current_minute = now.minute
        current_time_minutes = current_hour * 60 + current_minute
        
        # Only show if within resource-specific operating hours
        if operating_hours_start * 60 <= current_time_minutes < operating_hours_end * 60:
            current_time_info = {
                'hour': current_hour,
                'minute': current_minute,
                'minutes_from_midnight': current_time_minutes,
                'minutes_from_start': current_time_minutes - (operating_hours_start * 60)
            }
    
    # Process bookings for calendar display
    approved_bookings = []
    booked_slots = {}  # Key: date_iso, Value: list of {start_minutes, end_minutes}
    
    # Calculate time range for bookings
    if selected_day:
        target_date = date(selected_year, selected_month, selected_day)
        range_start = datetime.combine(target_date, dt_time(0, 0))
        range_end = datetime.combine(target_date, dt_time(23, 59))
    else:
        range_start = datetime.combine(month_start, dt_time(0, 0))
        range_end = datetime.combine(month_end, dt_time(23, 59))
    
    # Process each booking
    for booking in approved_bookings_raw:
        if booking.get('start_datetime') and booking.get('end_datetime'):
            try:
                # Parse and convert to EST
                start_dt = parse_datetime_aware(booking['start_datetime'])
                end_dt = parse_datetime_aware(booking['end_datetime'])
                
                start_dt_est = convert_to_est(start_dt)
                end_dt_est = convert_to_est(end_dt)
                
                # Convert range_start and range_end to UTC for comparison
                est_tz = gettz('America/New_York')
                range_start_utc = range_start.replace(tzinfo=est_tz).astimezone(tzutc()) if range_start.tzinfo is None else range_start.astimezone(tzutc())
                range_end_utc = range_end.replace(tzinfo=est_tz).astimezone(tzutc()) if range_end.tzinfo is None else range_end.astimezone(tzutc())
                
                # Only include bookings that overlap with the selected range
                if start_dt < range_end_utc and end_dt > range_start_utc:
                    # Store formatted booking
                    approved_bookings.append({
                        'booking_id': booking.get('booking_id'),
                        'start_datetime': booking['start_datetime'],
                        'end_datetime': booking['end_datetime'],
                        'start_dt': start_dt_est,
                        'end_dt': end_dt_est,
                        'date': start_dt_est.date().isoformat(),
                        'start_time': start_dt_est.strftime('%H:%M'),
                        'end_time': end_dt_est.strftime('%H:%M'),
                        'start_hour': start_dt_est.hour,
                        'end_hour': end_dt_est.hour,
                        'start_minute': start_dt_est.minute,
                        'end_minute': end_dt_est.minute,
                        'weekday': start_dt_est.weekday(),
                        'status': booking.get('status', 'approved')
                    })
                    
                    # Add to booked slots
                    date_key = start_dt_est.date().isoformat()
                    if date_key not in booked_slots:
                        booked_slots[date_key] = []
                    
                    start_minutes = start_dt_est.hour * 60 + start_dt_est.minute
                    end_minutes = end_dt_est.hour * 60 + end_dt_est.minute
                    booked_slots[date_key].append({
                        'start_minutes': start_minutes,
                        'end_minutes': end_minutes,
                        'start_time': start_dt_est.strftime('%H:%M'),
                        'end_time': end_dt_est.strftime('%H:%M')
                    })
            except (ValueError, TypeError, AttributeError) as e:
                logger.warning(f"Skipping invalid booking date: {e}")
                # Skip invalid dates
                continue
    
    # Sort bookings by start time
    approved_bookings.sort(key=lambda x: x['start_dt'] if 'start_dt' in x else datetime.now())
    
    # Generate calendar data based on view type
    if selected_day:
        # Day view - generate hourly slots for the selected day
        day_date = date(selected_year, selected_month, selected_day)
        date_key = day_date.isoformat()
        day_bookings = [b for b in approved_bookings if b['date'] == date_key]
        booked_times = booked_slots.get(date_key, [])
        
        # Generate time slots from 12 AM (00:00) to 11:59 PM (23:59) for all resources
        # Slots outside operating hours will be marked as unavailable
        day_time_slots = []
        
        # Always show all hours from 0 (12 AM) to 23 (11 PM)
        for hour in range(0, 24):  # 0 to 23 (12 AM to 11 PM)
            for minute in [0, 30]:
                slot_start_minutes = hour * 60 + minute
                slot_end_minutes = slot_start_minutes + 30
                
                # Check if slot is available
                is_available = True
                
                # Check for booking conflicts
                for booked in booked_times:
                    if slot_start_minutes < booked['end_minutes'] and slot_end_minutes > booked['start_minutes']:
                        is_available = False
                        break
                
                # For non-24-hour resources, mark slots outside operating hours as unavailable
                if not is_24_hours:
                    # Slot must start at or after operating hours start
                    if slot_start_minutes < (operating_hours_start * 60):
                        is_available = False
                    
                    # Slot must end at or before operating hours end
                    # If end time is 22:00 (10 PM), slot ending at 22:30 is not allowed
                    if slot_end_minutes > (operating_hours_end * 60):
                        is_available = False
                    
                    # Also check if slot starts at or after the closing time
                    if slot_start_minutes >= (operating_hours_end * 60):
                        is_available = False
                
                # Only show slots at least configured advance hours in the future from now
                min_advance_hours = Config.BOOKING_MIN_ADVANCE_HOURS
                slot_datetime = datetime.combine(day_date, dt_time(hour=hour, minute=minute))
                if slot_datetime < now + timedelta(hours=min_advance_hours):
                    is_available = False
                
                # For the last slot of the day (23:30), end time should be 23:59 instead of 00:00 (next day)
                display_end_hour = slot_end_minutes // 60
                display_end_minute = slot_end_minutes % 60
                if slot_end_minutes >= 1440:  # If it would roll over to next day
                    display_end_hour = 23
                    display_end_minute = 59
                
                day_time_slots.append({
                    'hour': hour,
                    'minute': minute,
                    'time_minutes': slot_start_minutes,
                    'start_time': f"{hour:02d}:{minute:02d}",
                    'end_time': f"{display_end_hour:02d}:{display_end_minute:02d}",
                    'is_available': is_available,
                    'is_booked': not is_available
                })
        
        day_data = {
            'date': day_date,
            'date_iso': date_key,
            'day_name': day_date.strftime('%A'),
            'day_num': day_date.day,
            'month': day_date.strftime('%B'),
            'year': day_date.year,
            'is_today': day_date == today,
            'bookings': day_bookings,
            'time_slots': day_time_slots,
            'booked_slots': booked_times
        }
        
        calendar_data = None
        month_calendar = None
    else:
        # Month view - generate calendar grid
        calendar_grid = []
        for week in month_calendar:
            week_row = []
            for day_num in week:
                if day_num == 0:
                    week_row.append(None)
                else:
                    day_date = date(selected_year, selected_month, day_num)
                    date_key = day_date.isoformat()
                    day_bookings = [b for b in approved_bookings if b['date'] == date_key]
                    booked_count = len(day_bookings)
                    
                    is_past = day_date < today
                    is_today = day_date == today
                    is_selectable = day_date >= today
                    
                    week_row.append({
                        'day': day_num,
                        'date': day_date,
                        'date_iso': date_key,
                        'is_today': is_today,
                        'is_past': is_past,
                        'is_selectable': is_selectable,
                        'bookings_count': booked_count,
                        'has_bookings': booked_count > 0
                    })
            calendar_grid.append(week_row)
        
        day_data = None
        calendar_data = calendar_grid
    
    return {
        'calendar_data': calendar_data,
        'day_data': day_data,
        'booked_slots': booked_slots,
        'approved_bookings': approved_bookings,
        'prev_year': prev_year,
        'prev_month': prev_month,
        'next_year': next_year,
        'next_month': next_month,
        'can_go_prev': can_go_prev,
        'current_time_info': current_time_info
    }

