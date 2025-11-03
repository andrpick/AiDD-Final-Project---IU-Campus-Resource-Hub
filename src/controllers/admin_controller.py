"""
Admin controller (Flask blueprint).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from src.services.admin_service import (
    get_statistics, list_users, suspend_user, unsuspend_user,
    change_user_role, delete_user, get_admin_logs, get_user, update_user
)
from src.services.resource_service import list_resources, update_resource, get_resource
from src.services.booking_service import list_bookings, get_booking, update_booking

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to require admin role."""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Admin access required.', 'error')
            return redirect(url_for('home'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard."""
    # Get filter parameters for popular resources
    category_filter = request.args.get('category', '').strip() or None
    location_filter = request.args.get('location', '').strip() or None
    featured_filter = request.args.get('featured', '').strip()
    featured = None
    if featured_filter == '1':
        featured = True
    elif featured_filter == '0':
        featured = False
    
    # Get sort parameter
    sort_by = request.args.get('sort_by', 'booking_count').strip()
    sort_order = request.args.get('sort_order', 'desc').strip()
    
    result = get_statistics(category_filter=category_filter, location_filter=location_filter, 
                           featured_filter=featured, sort_by=sort_by, sort_order=sort_order)
    
    if result['success']:
        stats = result['data']
        return render_template('admin/dashboard.html', 
                             stats=stats,
                             category_filter=category_filter,
                             location_filter=location_filter,
                             featured_filter=featured_filter,
                             sort_by=sort_by,
                             sort_order=sort_order)
    else:
        return render_template('admin/dashboard.html', 
                             stats={},
                             category_filter=None,
                             location_filter=None,
                             featured_filter=None,
                             sort_by='booking_count',
                             sort_order='desc')

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    """List all users."""
    role = request.args.get('role', '').strip() or None
    suspended_arg = request.args.get('suspended', '').strip()
    # Properly handle suspended filter: empty = None, "1" = True, "0" = False
    suspended = None
    if suspended_arg == '1':
        suspended = True
    elif suspended_arg == '0':
        suspended = False
    # If suspended_arg is empty or anything else, suspended stays None
    
    department = request.args.get('department', '').strip() or None
    search = request.args.get('search', '').strip() or None
    page = request.args.get('page', 1, type=int)
    page_size = min(100, max(1, request.args.get('page_size', 20, type=int)))
    offset = (page - 1) * page_size
    
    result = list_users(role=role, suspended=suspended, department=department,
                       search=search, limit=page_size, offset=offset)
    
    if result['success']:
        data = result['data']
        users = data['users']
        total = data['total']
        total_pages = (total + page_size - 1) // page_size
        
        return render_template('admin/users.html',
                             users=users,
                             page=page,
                             total_pages=total_pages,
                             total=total,
                             role_filter=role,
                             suspended_filter=suspended,
                             department_filter=department,
                             search_query=search)
    else:
        return render_template('admin/users.html', users=[], page=1, total_pages=0, total=0,
                             role_filter=None, suspended_filter=None, department_filter=None, search_query=None)

@admin_bp.route('/users/<int:user_id>/suspend', methods=['POST'])
@login_required
@admin_required
def suspend(user_id):
    """Suspend a user."""
    reason = request.form.get('reason', '').strip()
    
    if not reason:
        flash('Suspension reason is required.', 'error')
        return redirect(url_for('admin.users'))
    
    result = suspend_user(user_id, current_user.user_id, reason)
    
    if result['success']:
        flash('User suspended.', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/unsuspend', methods=['POST'])
@login_required
@admin_required
def unsuspend(user_id):
    """Unsuspend a user."""
    result = unsuspend_user(user_id, current_user.user_id)
    
    if result['success']:
        flash('User unsuspended.', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/role', methods=['POST'])
@login_required
@admin_required
def change_role(user_id):
    """Change user role."""
    new_role = request.form.get('role', '').strip()
    
    if not new_role:
        flash('Role is required.', 'error')
        return redirect(url_for('admin.users'))
    
    result = change_user_role(user_id, new_role, current_user.user_id)
    
    if result['success']:
        flash(f'User role changed to {new_role}.', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete(user_id):
    """Delete a user."""
    result = delete_user(user_id, current_user.user_id)
    
    if result['success']:
        flash('User deleted.', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    """View and edit user details."""
    if request.method == 'POST':
        # Get form data
        # Required fields - always sent
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        role = request.form.get('role', '').strip()
        
        # Optional fields
        password = request.form.get('password', '').strip() or None  # None means don't change
        department = request.form.get('department', '').strip()  # Empty string means clear
        profile_image = request.form.get('profile_image', '').strip()  # Empty string means clear
        
        suspended_str = request.form.get('suspended', '').strip()
        suspended = None
        if suspended_str == '1':
            suspended = True
        elif suspended_str == '0':
            suspended = False
        suspended_reason = request.form.get('suspended_reason', '').strip() or None
        
        # Update user - always send required fields
        # For optional fields: send empty string to clear, None to skip
        result = update_user(
            user_id=user_id,
            admin_id=current_user.user_id,
            name=name,
            email=email,
            password=password,
            role=role,
            department=department,  # Empty string will clear, non-empty will set
            profile_image=profile_image,  # Empty string will clear, non-empty will set
            suspended=suspended,
            suspended_reason=suspended_reason
        )
        
        if result['success']:
            flash('User updated successfully.', 'success')
            return redirect(url_for('admin.users'))
        else:
            flash(result['error'], 'error')
            # Fall through to GET to show form with errors
    
    # GET request - show edit form
    result = get_user(user_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('admin.users'))
    
    user = result['data']
    return render_template('admin/user_edit.html', user=user)

@admin_bp.route('/logs')
@login_required
@admin_required
def logs():
    """View admin logs."""
    admin_id = request.args.get('admin_id', type=int)
    action = request.args.get('action', '').strip() or None
    page = request.args.get('page', 1, type=int)
    page_size = min(100, max(1, request.args.get('page_size', 50, type=int)))
    offset = (page - 1) * page_size
    
    result = get_admin_logs(admin_id=admin_id, action=action, limit=page_size, offset=offset)
    
    if result['success']:
        data = result['data']
        logs = data['logs']
        total = data['total']
        total_pages = (total + page_size - 1) // page_size
        
        return render_template('admin/logs.html',
                             logs=logs,
                             page=page,
                             total_pages=total_pages,
                             total=total,
                             admin_id_filter=admin_id,
                             action_filter=action)
    else:
        return render_template('admin/logs.html', logs=[], page=1, total_pages=0, total=0)

@admin_bp.route('/resources')
@login_required
@admin_required
def resources():
    """List all resources for admin management."""
    page = request.args.get('page', 1, type=int)
    page_size = min(100, max(1, request.args.get('page_size', 20, type=int)))
    offset = (page - 1) * page_size
    status_filter = request.args.get('status', '').strip() or None
    
    result = list_resources(status=status_filter, limit=page_size, offset=offset)
    
    if result['success']:
        resources_list = result['data']['resources']
        total = result['data']['total']
        total_pages = (total + page_size - 1) // page_size
        return render_template('admin/resources.html',
                             resources=resources_list,
                             page=page,
                             total_pages=total_pages,
                             total=total,
                             status_filter=status_filter)
    else:
        return render_template('admin/resources.html', resources=[], page=1, total_pages=0, total=0, status_filter=status_filter)

@admin_bp.route('/resources/<int:resource_id>/feature', methods=['POST'])
@login_required
@admin_required
def feature_resource(resource_id):
    """Feature a resource on the homepage."""
    result = update_resource(resource_id, featured=1)
    
    if result['success']:
        # Log admin action
        from src.data_access.database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO admin_logs (admin_id, action, target_table, target_id, details)
                VALUES (?, 'feature_resource', 'resources', ?, 'Resource featured on homepage')
            """, (current_user.user_id, resource_id))
            conn.commit()
        
        flash('Resource featured on homepage.', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('admin.resources'))

@admin_bp.route('/resources/<int:resource_id>/unfeature', methods=['POST'])
@login_required
@admin_required
def unfeature_resource(resource_id):
    """Unfeature a resource from the homepage."""
    result = update_resource(resource_id, featured=0)
    
    if result['success']:
        # Log admin action
        from src.data_access.database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO admin_logs (admin_id, action, target_table, target_id, details)
                VALUES (?, 'unfeature_resource', 'resources', ?, 'Resource removed from homepage')
            """, (current_user.user_id, resource_id))
            conn.commit()
        
        flash('Resource removed from homepage.', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('admin.resources'))

@admin_bp.route('/resources/<int:resource_id>/archive', methods=['POST'])
@login_required
@admin_required
def archive_resource(resource_id):
    """Archive a resource."""
    from src.services.resource_service import delete_resource
    
    result = delete_resource(resource_id)
    
    if result['success']:
        # Log admin action
        from src.data_access.database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO admin_logs (admin_id, action, target_table, target_id, details)
                VALUES (?, 'archive_resource', 'resources', ?, 'Resource archived')
            """, (current_user.user_id, resource_id))
            conn.commit()
        
        flash('Resource archived successfully.', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('admin.resources'))

@admin_bp.route('/resources/<int:resource_id>/unarchive', methods=['POST'])
@login_required
@admin_required
def unarchive_resource(resource_id):
    """Unarchive a resource (set status back to published)."""
    result = update_resource(resource_id, status='published')
    
    if result['success']:
        # Log admin action
        from src.data_access.database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO admin_logs (admin_id, action, target_table, target_id, details)
                VALUES (?, 'unarchive_resource', 'resources', ?, 'Resource unarchived (set to published)')
            """, (current_user.user_id, resource_id))
            conn.commit()
        
        flash('Resource unarchived successfully.', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('admin.resources'))

@admin_bp.route('/bookings')
@login_required
@admin_required
def bookings():
    """List all bookings for admin management."""
    from datetime import datetime
    from dateutil.tz import tzutc
    from src.services.booking_service import list_bookings
    from src.services.resource_service import get_resource
    from src.models.user import User
    
    status_filter = request.args.get('status', '').strip() or None
    resource_id = request.args.get('resource_id', type=int)
    
    # Get all bookings (ignore pagination for sectioning, but limit to reasonable amount)
    result = list_bookings(resource_id=resource_id, status=status_filter, limit=1000, offset=0)
    
    if result['success']:
        all_bookings = result['data']['bookings']
        total = result['data']['total']
        
        # Helper function to parse datetime (same as bookings_controller)
        def _parse_datetime_aware(dt_str):
            """Parse datetime string and ensure it's timezone-aware (UTC)."""
            from dateutil.tz import tzutc
            from dateutil import parser
            
            try:
                dt = parser.parse(dt_str.replace('Z', '+00:00'))
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=tzutc())
                else:
                    # Convert to UTC if timezone-aware
                    dt = dt.astimezone(tzutc())
                return dt
            except Exception:
                # Return a very old datetime as fallback for sorting
                return datetime(1970, 1, 1, tzinfo=tzutc())
        
        # Get current time in UTC
        now = datetime.now(tzutc())
        
        # Separate bookings into three categories (same logic as user bookings)
        upcoming_bookings = []  # Approved bookings that haven't started yet
        previous_bookings = []  # Approved bookings that have passed OR completed bookings
        canceled_bookings = []  # Canceled bookings regardless of date
        
        for booking in all_bookings:
            try:
                # Parse booking start datetime
                start_dt = _parse_datetime_aware(booking['start_datetime'])
                
                if booking['status'] == 'cancelled':
                    # Canceled bookings go to canceled section
                    canceled_bookings.append(booking)
                elif booking['status'] == 'approved' and start_dt >= now:
                    # Upcoming approved bookings
                    upcoming_bookings.append(booking)
                elif booking['status'] == 'approved' and start_dt < now:
                    # Previous approved bookings (past their start time)
                    previous_bookings.append(booking)
                elif booking['status'] == 'completed':
                    # Completed bookings go to previous section
                    previous_bookings.append(booking)
                else:
                    # Any other status goes to previous section
                    previous_bookings.append(booking)
            except Exception:
                # If parsing fails, treat as previous booking
                if booking['status'] == 'cancelled':
                    canceled_bookings.append(booking)
                else:
                    previous_bookings.append(booking)
        
        # Sort upcoming by start_datetime ASC (soonest first)
        upcoming_bookings.sort(key=lambda b: _parse_datetime_aware(b['start_datetime']))
        
        # Sort previous by start_datetime DESC (most recent first)
        previous_bookings.sort(key=lambda b: _parse_datetime_aware(b['start_datetime']), reverse=True)
        
        # Sort canceled by start_datetime DESC (most recent first)
        canceled_bookings.sort(key=lambda b: _parse_datetime_aware(b['start_datetime']), reverse=True)
        
        # Enrich with resource and user info
        for booking in upcoming_bookings + previous_bookings + canceled_bookings:
            resource_result = get_resource(booking['resource_id'])
            if resource_result['success']:
                booking['resource'] = resource_result['data']
            
            user = User.get(booking['requester_id'])
            if user:
                booking['requester'] = {
                    'user_id': user.user_id,
                    'name': user.name,
                    'email': user.email
                }
        
        return render_template('admin/bookings.html',
                             upcoming_bookings=upcoming_bookings,
                             previous_bookings=previous_bookings,
                             canceled_bookings=canceled_bookings,
                             total=total,
                             status_filter=status_filter,
                             resource_id_filter=resource_id)
    else:
        return render_template('admin/bookings.html', 
                             upcoming_bookings=[],
                             previous_bookings=[],
                             canceled_bookings=[],
                             total=0,
                             status_filter=status_filter, 
                             resource_id_filter=resource_id)

@admin_bp.route('/bookings/<int:booking_id>')
@login_required
@admin_required
def booking_detail(booking_id):
    """View and edit booking details."""
    result = get_booking(booking_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('admin.bookings'))
    
    booking = result['data']
    
    # Get resource and user info
    from src.services.resource_service import get_resource
    from src.models.user import User
    
    resource_result = get_resource(booking['resource_id'])
    resource = resource_result['data'] if resource_result['success'] else None
    
    user = User.get(booking['requester_id'])
    requester = {
        'user_id': user.user_id,
        'name': user.name,
        'email': user.email
    } if user else None
    
    return render_template('admin/booking_detail.html', booking=booking, resource=resource, requester=requester)

@admin_bp.route('/bookings/<int:booking_id>/update', methods=['POST'])
@login_required
@admin_required
def update_booking_admin(booking_id):
    """Update booking fields (admin can overwrite)."""
    from dateutil import parser
    from dateutil.tz import gettz, tzutc
    from datetime import datetime
    
    start_datetime_str = request.form.get('start_datetime', '').strip() or None
    end_datetime_str = request.form.get('end_datetime', '').strip() or None
    status = request.form.get('status', '').strip() or None
    skip_validation = request.form.get('skip_validation') == 'on'
    
    # Validate status
    if status and status not in ['approved', 'cancelled', 'completed']:
        flash('Invalid status.', 'error')
        return redirect(url_for('admin.booking_detail', booking_id=booking_id))
    
    # Convert datetime-local input (EST/EDT) to UTC for storage
    start_datetime = None
    end_datetime = None
    
    if start_datetime_str:
        try:
            # Parse as local time (EST/EDT)
            est_tz = gettz('America/New_York')
            dt_local = datetime.strptime(start_datetime_str, '%Y-%m-%dT%H:%M')
            dt_local = dt_local.replace(tzinfo=est_tz)
            # Convert to UTC
            dt_utc = dt_local.astimezone(tzutc())
            start_datetime = dt_utc.isoformat()
        except Exception as e:
            flash(f'Invalid start datetime format: {str(e)}', 'error')
            return redirect(url_for('admin.booking_detail', booking_id=booking_id))
    
    if end_datetime_str:
        try:
            # Parse as local time (EST/EDT)
            est_tz = gettz('America/New_York')
            dt_local = datetime.strptime(end_datetime_str, '%Y-%m-%dT%H:%M')
            dt_local = dt_local.replace(tzinfo=est_tz)
            # Convert to UTC
            dt_utc = dt_local.astimezone(tzutc())
            end_datetime = dt_utc.isoformat()
        except Exception as e:
            flash(f'Invalid end datetime format: {str(e)}', 'error')
            return redirect(url_for('admin.booking_detail', booking_id=booking_id))
    
    result = update_booking(booking_id, start_datetime=start_datetime, end_datetime=end_datetime,
                           status=status, skip_validation=skip_validation)
    
    if result['success']:
        # Log admin action
        from src.data_access.database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            details = f"Booking updated by admin"
            if start_datetime or end_datetime:
                details += f" (datetime changed)"
            if status:
                details += f" (status: {status})"
            
            cursor.execute("""
                INSERT INTO admin_logs (admin_id, action, target_table, target_id, details)
                VALUES (?, 'update_booking', 'bookings', ?, ?)
            """, (current_user.user_id, booking_id, details))
            conn.commit()
        
        flash('Booking updated successfully.', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('admin.booking_detail', booking_id=booking_id))

