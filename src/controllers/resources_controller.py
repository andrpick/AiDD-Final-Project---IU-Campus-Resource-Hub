"""
Resources controller (Flask blueprint).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from src.services.resource_service import create_resource, get_resource, update_resource, delete_resource, list_resources
from src.services.review_service import get_resource_reviews
from src.services.booking_service import list_bookings
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid
import json

resources_bp = Blueprint('resources', __name__, url_prefix='/resources')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@resources_bp.route('/')
def index():
    """Redirect to search page (resources browsing is now handled by search)."""
    from flask import redirect, url_for
    return redirect(url_for('search.index'))

@resources_bp.route('/<int:resource_id>')
def detail(resource_id):
    """View resource details."""
    result = get_resource(resource_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('search.index'))
    
    resource = result['data']
    
    # Only show published resources or owner's draft resources
    if resource['status'] != 'published':
        if not current_user.is_authenticated or resource['owner_id'] != current_user.user_id:
            flash('Resource not found.', 'error')
            return redirect(url_for('search.index'))
    
    # Fetch a few recent reviews (up to 3) and review stats
    reviews_result = get_resource_reviews(resource_id, limit=3, offset=0)
    if reviews_result['success']:
        reviews = reviews_result['data']['reviews']
        review_stats = reviews_result['data']['stats']
        total_reviews = reviews_result['data']['total']
    else:
        reviews = []
        review_stats = None
        total_reviews = 0
    
    # Fetch approved bookings for the resource schedule
    from datetime import timedelta, date
    from calendar import monthrange, monthcalendar
    now = datetime.now()
    today = now.date()
    
    # Get month and day from query parameters (default to current month)
    selected_year = request.args.get('year', today.year, type=int)
    selected_month = request.args.get('month', today.month, type=int)
    selected_day = request.args.get('day', type=int)  # Optional - if provided, show day view
    
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
    
    # Check if we can navigate to previous month (cannot go before current month)
    can_go_prev = not (prev_year < today.year or (prev_year == today.year and prev_month < today.month))
    
    # Calculate current time position for today's indicator (only in month view)
    current_time_info = None
    if selected_year == today.year and selected_month == today.month:
        current_hour = now.hour
        current_minute = now.minute
        current_time_minutes = current_hour * 60 + current_minute
        
        # Only show if within operating hours (8 AM - 10 PM)
        if 8 * 60 <= current_time_minutes < 22 * 60:
            current_time_info = {
                'hour': current_hour,
                'minute': current_minute,
                'minutes_from_midnight': current_time_minutes,
                'minutes_from_8am': current_time_minutes - (8 * 60)
            }
    
    # Get all bookings for the selected month (or day if selected)
    approved_bookings_result = list_bookings(resource_id=resource_id, status='approved', limit=500, offset=0)
    pending_bookings_result = list_bookings(resource_id=resource_id, status='pending', limit=500, offset=0)
    
    all_bookings_raw = []
    if approved_bookings_result['success']:
        all_bookings_raw.extend(approved_bookings_result['data']['bookings'])
    if pending_bookings_result['success']:
        all_bookings_raw.extend(pending_bookings_result['data']['bookings'])
    
    # Process bookings for calendar display
    approved_bookings = []
    booked_slots = {}  # Key: date_iso, Value: list of {start_minutes, end_minutes}
    
    # Calculate time range for bookings (entire month if month view, single day if day view)
    if selected_day:
        # Day view - only show bookings for selected day
        target_date = date(selected_year, selected_month, selected_day)
        range_start = datetime.combine(target_date, datetime.min.time().replace(hour=0, minute=0))
        range_end = datetime.combine(target_date, datetime.min.time().replace(hour=23, minute=59))
    else:
        # Month view - show bookings for entire month
        range_start = datetime.combine(month_start, datetime.min.time().replace(hour=0, minute=0))
        range_end = datetime.combine(month_end, datetime.min.time().replace(hour=23, minute=59))
    
    for booking in all_bookings_raw:
        if booking.get('start_datetime') and booking.get('end_datetime'):
            try:
                # Parse datetime strings
                start_str = booking['start_datetime'].replace('Z', '+00:00') if 'Z' in booking['start_datetime'] else booking['start_datetime']
                end_str = booking['end_datetime'].replace('Z', '+00:00') if 'Z' in booking['end_datetime'] else booking['end_datetime']
                
                start_dt = datetime.fromisoformat(start_str)
                end_dt = datetime.fromisoformat(end_str)
                
                # Ensure datetimes are timezone-aware (assume UTC if naive)
                from dateutil.tz import gettz, tzutc
                if start_dt.tzinfo is None:
                    start_dt = start_dt.replace(tzinfo=tzutc())
                if end_dt.tzinfo is None:
                    end_dt = end_dt.replace(tzinfo=tzutc())
                
                # Convert to EST/EDT for display
                est_tz = gettz('America/New_York')
                start_dt_est = start_dt.astimezone(est_tz)
                end_dt_est = end_dt.astimezone(est_tz)
                
                # Make range_start and range_end timezone-aware for comparison
                # range_start and range_end are naive datetimes in local time, convert to UTC for comparison
                range_start_utc = range_start.replace(tzinfo=est_tz).astimezone(tzutc()) if range_start.tzinfo is None else range_start.astimezone(tzutc())
                range_end_utc = range_end.replace(tzinfo=est_tz).astimezone(tzutc()) if range_end.tzinfo is None else range_end.astimezone(tzutc())
                
                # Only include bookings that overlap with the selected range
                # A booking overlaps if: booking_start < range_end AND booking_end > range_start
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
                    
                    # Add to booked slots (convert to minutes from midnight in EST/EDT)
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
            except Exception as e:
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
        
        # Generate time slots from 8 AM to 10 PM in 30-minute increments
        day_time_slots = []
        operating_hours_start = 8
        operating_hours_end = 22
        
        for hour in range(operating_hours_start, operating_hours_end):
            for minute in [0, 30]:
                slot_start_minutes = hour * 60 + minute
                slot_end_minutes = slot_start_minutes + 30
                
                # Check if slot is available
                # A slot overlaps with a booking if:
                # - slot starts before booking ends AND slot ends after booking starts
                is_available = True
                for booked in booked_times:
                    # Check for overlap: slot_start < booked_end AND slot_end > booked_start
                    if slot_start_minutes < booked['end_minutes'] and slot_end_minutes > booked['start_minutes']:
                        is_available = False
                        break
                
                # Only show slots at least 1 hour in the future from now
                from datetime import time as dt_time
                slot_datetime = datetime.combine(day_date, dt_time(hour=hour, minute=minute))
                if slot_datetime < now + timedelta(hours=1):
                    is_available = False
                
                day_time_slots.append({
                    'hour': hour,
                    'minute': minute,
                    'time_minutes': slot_start_minutes,
                    'start_time': f"{hour:02d}:{minute:02d}",
                    'end_time': f"{(slot_end_minutes // 60):02d}:{(slot_end_minutes % 60):02d}",
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
                    # Day is outside the month
                    week_row.append(None)
                else:
                    day_date = date(selected_year, selected_month, day_num)
                    date_key = day_date.isoformat()
                    day_bookings = [b for b in approved_bookings if b['date'] == date_key]
                    booked_count = len(day_bookings)
                    
                    # Check if day is in the past or today (but not future)
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
    
    schedule_data = booked_slots  # Keep for backward compatibility
    
    return render_template('resources/detail.html', 
                         resource=resource, 
                         reviews=reviews,
                         review_stats=review_stats,
                         total_reviews=total_reviews,
                         approved_bookings=approved_bookings,
                         schedule_data=schedule_data,
                         calendar_data=calendar_data,
                         day_data=day_data,
                         selected_year=selected_year,
                         selected_month=selected_month,
                         selected_day=selected_day,
                         prev_year=prev_year,
                         prev_month=prev_month,
                         next_year=next_year,
                         next_month=next_month,
                         can_go_prev=can_go_prev,
                         today=today,
                         current_time_info=current_time_info)

@resources_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new resource."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip() or None
        category = request.form.get('category', '').strip()
        location = request.form.get('location', '').strip()
        has_capacity = request.form.get('has_capacity') == 'on'
        capacity = request.form.get('capacity', type=int) if has_capacity else None
        status = request.form.get('status', 'draft').strip()
        
        # Handle multiple image uploads
        images = []
        # Get all files with name 'image' (support multiple)
        uploaded_files = request.files.getlist('image')
        upload_folder = current_app.config['UPLOAD_FOLDER']
        resource_uploads = os.path.join(upload_folder, 'resources')
        os.makedirs(resource_uploads, exist_ok=True)
        
        for file in uploaded_files:
            if file and file.filename != '' and allowed_file(file.filename):
                # Generate unique filename
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{ext}"
                
                # Save file
                file_path = os.path.join(resource_uploads, unique_filename)
                file.save(file_path)
                
                # Store relative path for database
                images.append(f"resources/{unique_filename}")
        
        # Handle availability_rules (placeholder)
        availability_rules = request.form.get('availability_rules')
        
        result = create_resource(
            owner_id=current_user.user_id,
            title=title,
            description=description,
            category=category,
            location=location,
            capacity=capacity,
            images=images if images else None,
            availability_rules=availability_rules,
            status=status
        )
        
        if result['success']:
            flash('Resource created successfully.', 'success')
            return redirect(url_for('resources.detail', resource_id=result['data']['resource_id']))
        else:
            flash(result['error'], 'error')
    
    return render_template('resources/create.html')

@resources_bp.route('/<int:resource_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(resource_id):
    """Edit a resource."""
    result = get_resource(resource_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('search.index'))
    
    resource = result['data']
    
    # Permission check
    if resource['owner_id'] != current_user.user_id and not current_user.is_admin():
        flash('Unauthorized.', 'error')
        return redirect(url_for('resources.detail', resource_id=resource_id))
    
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip() or None
        category = request.form.get('category', '').strip()
        location = request.form.get('location', '').strip()
        has_capacity = request.form.get('has_capacity') == 'on'
        capacity = request.form.get('capacity', type=int) if has_capacity else None
        status = request.form.get('status', '').strip()
        
        # Only admin users can set status to 'archived'
        if status == 'archived' and not current_user.is_admin():
            flash('Only administrators can archive resources.', 'error')
            return redirect(url_for('resources.edit', resource_id=resource_id))
        
        updates = {
            'title': title,
            'description': description,
            'category': category,
            'location': location,
            'capacity': capacity,
            'status': status
        }
        
        # Handle multiple image uploads and removals
        existing_images = resource.get('images', [])
        if not isinstance(existing_images, list):
            try:
                existing_images = json.loads(existing_images) if existing_images else []
            except:
                existing_images = []
        
        # Handle image removal (admin only)
        images_removed = False
        if current_user.is_admin():
            remove_images = request.form.getlist('remove_images')
            if remove_images:
                images_removed = True
                # Filter out images to be removed
                existing_images = [img for img in existing_images if img not in remove_images]
                
                # Delete the actual image files from the server
                upload_folder = current_app.config['UPLOAD_FOLDER']
                for image_path in remove_images:
                    try:
                        full_path = os.path.join(upload_folder, image_path)
                        if os.path.exists(full_path):
                            os.remove(full_path)
                    except Exception as e:
                        # Log error but continue
                        print(f"Error deleting image {image_path}: {e}")
        
        # Get all new uploaded files
        uploaded_files = request.files.getlist('image')
        upload_folder = current_app.config['UPLOAD_FOLDER']
        resource_uploads = os.path.join(upload_folder, 'resources')
        os.makedirs(resource_uploads, exist_ok=True)
        
        new_images = []
        for file in uploaded_files:
            if file and file.filename != '' and allowed_file(file.filename):
                # Generate unique filename
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{ext}"
                
                # Save file
                file_path = os.path.join(resource_uploads, unique_filename)
                file.save(file_path)
                
                # Add to images list
                new_images.append(f"resources/{unique_filename}")
        
        # Combine existing (after removal) and new images
        if new_images:
            updates['images'] = existing_images + new_images
        elif images_removed:
            # Update images list even if no new images, to reflect removals
            updates['images'] = existing_images
        
        result = update_resource(resource_id, **updates)
        
        if result['success']:
            flash('Resource updated successfully.', 'success')
            return redirect(url_for('resources.detail', resource_id=resource_id))
        else:
            flash(result['error'], 'error')
    
    return render_template('resources/edit.html', resource=resource)

@resources_bp.route('/<int:resource_id>/publish', methods=['POST'])
@login_required
def publish(resource_id):
    """Publish a draft resource."""
    result = get_resource(resource_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('search.index'))
    
    resource = result['data']
    
    # Permission check
    if resource['owner_id'] != current_user.user_id and not current_user.is_admin():
        flash('Unauthorized.', 'error')
        return redirect(url_for('resources.detail', resource_id=resource_id))
    
    # Check if resource is already published
    if resource['status'] == 'published':
        flash('Resource is already published.', 'info')
        return redirect(url_for('resources.detail', resource_id=resource_id))
    
    result = update_resource(resource_id, status='published')
    
    if result['success']:
        flash('Resource published successfully.', 'success')
        return redirect(url_for('resources.detail', resource_id=resource_id))
    else:
        flash(result['error'], 'error')
        return redirect(url_for('resources.detail', resource_id=resource_id))

@resources_bp.route('/<int:resource_id>/delete', methods=['POST'])
@login_required
def delete(resource_id):
    """Delete a resource (soft delete - archive). Only admin users can archive resources."""
    result = get_resource(resource_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('search.index'))
    
    resource = result['data']
    
    # Only admin users can archive resources
    if not current_user.is_admin():
        flash('Only administrators can archive resources.', 'error')
        return redirect(url_for('resources.detail', resource_id=resource_id))
    
    result = delete_resource(resource_id)
    
    if result['success']:
        flash('Resource archived successfully.', 'success')
        return redirect(url_for('search.index'))
    else:
        flash(result['error'], 'error')
        return redirect(url_for('resources.detail', resource_id=resource_id))

@resources_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded images."""
    upload_folder = current_app.config['UPLOAD_FOLDER']
    return send_from_directory(upload_folder, filename)

@resources_bp.route('/my-resources')
@login_required
def my_resources():
    """List user's own resources."""
    page = request.args.get('page', 1, type=int)
    page_size = min(100, max(1, request.args.get('page_size', 20, type=int)))
    offset = (page - 1) * page_size
    status_filter = request.args.get('status', '').strip() or None
    
    result = list_resources(owner_id=current_user.user_id, status=status_filter, limit=page_size, offset=offset)
    
    if result['success']:
        resources = result['data']['resources']
        total = result['data']['total']
        total_pages = (total + page_size - 1) // page_size
        return render_template('resources/my_resources.html',
                             resources=resources,
                             page=page,
                             total_pages=total_pages,
                             total=total,
                             status_filter=status_filter)
    else:
        return render_template('resources/my_resources.html', resources=[], page=1, total_pages=0, total=0, status_filter=status_filter)

