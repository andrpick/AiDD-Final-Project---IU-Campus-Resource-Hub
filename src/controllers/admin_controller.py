"""
Admin controller (Flask blueprint).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from src.services.admin_service import (
    get_statistics, list_users, suspend_user, unsuspend_user,
    change_user_role, delete_user, get_admin_logs, get_user, update_user, restore_user, get_deleted_users
)
from src.services.resource_service import list_resources, update_resource, get_resource, reassign_resource_ownership
from src.services.booking_service import list_bookings, get_booking, update_booking, update_booking_status, check_conflicts
from src.services.messaging_service import get_deleted_threads, restore_thread, send_message
from src.utils.decorators import admin_required
from src.utils.controller_helpers import categorize_bookings, log_admin_action, parse_bool_filter
from src.utils.query_builder import QueryBuilder

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Admin dashboard."""
    result = get_statistics()
    
    if result['success']:
        stats = result['data']
        return render_template('admin/dashboard.html', stats=stats)
    else:
        return render_template('admin/dashboard.html', stats={})

@admin_bp.route('/statistics')
@login_required
@admin_required
def statistics():
    """Resource statistics page."""
    # Get filter parameters
    category_filter = request.args.get('category', '').strip() or None
    location_filter = request.args.get('location', '').strip() or None
    featured_filter = request.args.get('featured', '').strip()
    featured = parse_bool_filter(featured_filter)
    
    # Get sort parameter
    sort_by = request.args.get('sort_by', 'booking_count').strip()
    sort_order = request.args.get('sort_order', 'desc').strip()
    
    # Get pagination parameters
    page = request.args.get('page', 1, type=int)
    page_size = min(100, max(1, request.args.get('page_size', 25, type=int)))
    offset = (page - 1) * page_size
    
    result = get_statistics(category_filter=category_filter, location_filter=location_filter, 
                           featured_filter=featured, sort_by=sort_by, sort_order=sort_order)
    
    if result['success']:
        stats = result['data']
        popular_resources = stats.get('popular_resources', [])
        
        # Get total count and featured count from database (not limited by popular_resources LIMIT)
        from src.data_access.database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Build base query builder for filtering
            base_query = QueryBuilder('resources r')
            base_query.add_condition("r.status = 'published'")
            base_query.add_equals_filter('r.category', category_filter)
            if location_filter:
                base_query.add_like_filter('r.location', location_filter)
            if featured is not None:
                base_query.add_equals_filter('r.featured', 1 if featured else 0)
            
            # Get total count
            count_query, count_params = base_query.build_count_query('r.resource_id')
            cursor.execute(count_query, count_params)
            total_result = cursor.fetchone()
            total_resources = total_result[0] if total_result else 0
            
            # Get featured count - add featured condition
            featured_query = QueryBuilder('resources r')
            featured_query.add_condition("r.status = 'published'")
            featured_query.add_equals_filter('r.category', category_filter)
            if location_filter:
                featured_query.add_like_filter('r.location', location_filter)
            featured_query.add_equals_filter('r.featured', 1)
            featured_count_query, featured_count_params = featured_query.build_count_query('r.resource_id')
            cursor.execute(featured_count_query, featured_count_params)
            featured_result = cursor.fetchone()
            featured_count = featured_result[0] if featured_result else 0
            
            # Get all resources (not just top 10) for pagination
            sort_direction = 'DESC' if sort_order.lower() == 'desc' else 'ASC'
            valid_sort_fields = ['booking_count', 'review_count', 'avg_rating', 'title', 'category', 'location']
            if sort_by not in valid_sort_fields:
                sort_by = 'booking_count'
            
            # Build main query with aggregations
            main_query = QueryBuilder(
                'resources r',
                base_select="""SELECT 
                    r.resource_id, 
                    r.title, 
                    r.category,
                    r.location,
                    r.capacity,
                    r.featured,
                    COUNT(DISTINCT b.booking_id) as booking_count,
                    COUNT(DISTINCT rev.review_id) as review_count,
                    AVG(rev.rating) as avg_rating
                    FROM resources r"""
            )
            main_query.add_join("LEFT JOIN bookings b ON r.resource_id = b.resource_id")
            main_query.add_join("LEFT JOIN reviews rev ON r.resource_id = rev.resource_id")
            main_query.add_condition("r.status = 'published'")
            main_query.add_equals_filter('r.category', category_filter)
            if location_filter:
                main_query.add_like_filter('r.location', location_filter)
            if featured is not None:
                main_query.add_equals_filter('r.featured', 1 if featured else 0)
            main_query.set_group_by('r.resource_id, r.title, r.category, r.location, r.capacity, r.featured')
            # Order by requires a single column, so we'll handle complex ordering manually
            main_query.order_by = f"{sort_by} {sort_direction}, booking_count DESC"
            main_query.set_pagination(page_size, offset)
            
            query, query_params = main_query.build()
            cursor.execute(query, query_params)
            all_resources_raw = cursor.fetchall()
            
            # Process resources
            all_resources = []
            for row in all_resources_raw:
                resource = dict(row)
                if resource.get('avg_rating'):
                    resource['avg_rating'] = float(resource['avg_rating'])
                else:
                    resource['avg_rating'] = None
                all_resources.append(resource)
            
            # Calculate resource-specific statistics for summary cards
            # IMPORTANT: These are GLOBAL statistics, not filtered by category/location/featured
            # 1. Average rating across all resources (only resources with reviews)
            cursor.execute("""
                SELECT AVG(rating) as avg_rating
                FROM reviews
            """)
            avg_rating_result = cursor.fetchone()
            avg_rating_all = float(avg_rating_result['avg_rating']) if avg_rating_result and avg_rating_result['avg_rating'] else None
            
            # 2. Most booked resource (top resource by booking count) - GLOBAL, not filtered
            # This query ensures we get the resource with the highest booking count
            # In case of ties, it picks alphabetically first by title for consistency
            # Counts ALL bookings (historical), not just approved
            cursor.execute("""
                SELECT r.resource_id, r.title, COUNT(DISTINCT b.booking_id) as booking_count
                FROM resources r
                LEFT JOIN bookings b ON r.resource_id = b.resource_id
                WHERE r.status = 'published'
                GROUP BY r.resource_id, r.title
                ORDER BY booking_count DESC, r.title ASC
                LIMIT 1
            """)
            most_booked_result = cursor.fetchone()
            most_booked_resource = None
            most_booked_count = 0
            if most_booked_result and most_booked_result['booking_count']:
                most_booked_resource = most_booked_result['title']
                most_booked_count = most_booked_result['booking_count']
            
            # 3. Top rated resource (highest average rating with at least 1 review) - GLOBAL, not filtered
            cursor.execute("""
                SELECT r.resource_id, r.title, AVG(rev.rating) as avg_rating, COUNT(rev.review_id) as review_count
                FROM resources r
                LEFT JOIN reviews rev ON r.resource_id = rev.resource_id
                WHERE r.status = 'published'
                GROUP BY r.resource_id, r.title
                HAVING COUNT(rev.review_id) >= 1
                ORDER BY avg_rating DESC, review_count DESC, r.title ASC
                LIMIT 1
            """)
            top_rated_result = cursor.fetchone()
            top_rated_resource = None
            top_rated_rating = None
            if top_rated_result and top_rated_result['avg_rating']:
                top_rated_resource = top_rated_result['title']
                top_rated_rating = float(top_rated_result['avg_rating'])
            
            # 4. Average bookings per resource (only published resources) - GLOBAL, not filtered
            # Counts ALL bookings (historical), not just approved
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT r.resource_id) as resource_count,
                    COUNT(DISTINCT b.booking_id) as total_bookings
                FROM resources r
                LEFT JOIN bookings b ON r.resource_id = b.resource_id
                WHERE r.status = 'published'
            """)
            avg_bookings_result = cursor.fetchone()
            avg_bookings_per_resource = None
            if avg_bookings_result:
                resource_count = avg_bookings_result['resource_count'] or 1
                total_bookings = avg_bookings_result['total_bookings'] or 0
                avg_bookings_per_resource = round(total_bookings / resource_count, 1) if resource_count > 0 else 0
        
        # Paginate resources
        paginated_resources = all_resources
        total_pages = (total_resources + page_size - 1) // page_size
        
        # Resource-specific statistics summary
        resource_stats = {
            'avg_rating_all': avg_rating_all,
            'most_booked_resource': most_booked_resource,
            'most_booked_count': most_booked_count,
            'top_rated_resource': top_rated_resource,
            'top_rated_rating': top_rated_rating,
            'avg_bookings_per_resource': avg_bookings_per_resource
        }
        
        return render_template('admin/statistics.html', 
                             stats=stats,
                             resources=paginated_resources,
                             featured_count=featured_count,
                             resource_stats=resource_stats,
                             page=page,
                             total_pages=total_pages,
                             total=total_resources,
                             category_filter=category_filter,
                             location_filter=location_filter,
                             featured_filter=featured_filter,
                             sort_by=sort_by,
                             sort_order=sort_order)
    else:
        return render_template('admin/statistics.html', 
                             stats={},
                             resources=[],
                             featured_count=0,
                             resource_stats={
                                 'avg_rating_all': None,
                                 'most_booked_resource': None,
                                 'most_booked_count': 0,
                                 'top_rated_resource': None,
                                 'top_rated_rating': None,
                                 'avg_bookings_per_resource': 0
                             },
                             page=1,
                             total_pages=0,
                             total=0,
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
    # Get filter parameters
    role = request.args.get('role', '').strip() or None
    suspended_arg = request.args.get('suspended', '').strip()
    suspended = parse_bool_filter(suspended_arg)
    department = request.args.get('department', '').strip() or None
    search = request.args.get('search', '').strip() or None
    include_deleted = request.args.get('include_deleted', '').strip() == '1'
    page = request.args.get('page', 1, type=int)
    page_size = min(100, max(1, request.args.get('page_size', 25, type=int)))
    offset = (page - 1) * page_size
    
    result = list_users(role=role, suspended=suspended, department=department,
                       search=search, limit=page_size, offset=offset, include_deleted=include_deleted)
    
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
                             search_query=search,
                             include_deleted=include_deleted)
    else:
        return render_template('admin/users.html', users=[], page=1, total_pages=0, total=0,
                             role_filter=None, suspended_filter=None, department_filter=None, search_query=None,
                             include_deleted=False)

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

@admin_bp.route('/users/<int:user_id>/restore', methods=['POST'])
@login_required
@admin_required
def restore_user_route(user_id):
    """Restore a soft-deleted user."""
    result = restore_user(user_id, current_user.user_id)
    
    if result['success']:
        flash('User restored. Note: Email, name, and password were anonymized and need to be manually restored.', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('admin.restore'))

@admin_bp.route('/restore')
@login_required
@admin_required
def restore():
    """Data restore management page."""
    # Get deleted users
    users_result = get_deleted_users(limit=100, offset=0)
    deleted_users = users_result['data']['users'] if users_result['success'] else []
    deleted_users_count = users_result['data']['total'] if users_result['success'] else 0
    
    # Get deleted threads
    threads_result = get_deleted_threads(current_user.user_id, limit=100, offset=0)
    deleted_threads = threads_result['data']['threads'] if threads_result['success'] else []
    deleted_threads_count = threads_result['data']['total'] if threads_result['success'] else 0
    
    return render_template('admin/restore.html',
                         deleted_users=deleted_users,
                         deleted_users_count=deleted_users_count,
                         deleted_threads=deleted_threads,
                         deleted_threads_count=deleted_threads_count)

@admin_bp.route('/restore/thread/<int:thread_id>', methods=['POST'])
@login_required
@admin_required
def restore_thread_admin(thread_id):
    """Restore a deleted thread (admin route)."""
    result = restore_thread(thread_id, current_user.user_id)
    
    if result['success']:
        flash(f'Thread restored ({result["data"]["restored_count"]} messages restored).', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('admin.restore'))

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
    from src.models.user import User
    
    admin_id = request.args.get('admin_id', type=int)
    action = request.args.get('action', '').strip() or None
    target_table = request.args.get('target_table', '').strip() or None
    page = request.args.get('page', 1, type=int)
    page_size = min(100, max(1, request.args.get('page_size', 50, type=int)))
    offset = (page - 1) * page_size
    
    result = get_admin_logs(admin_id=admin_id, action=action, target_table=target_table, limit=page_size, offset=offset)
    
    if result['success']:
        data = result['data']
        logs = data['logs']
        total = data['total']
        total_pages = (total + page_size - 1) // page_size
        
        # Get list of admins for filter dropdown
        from src.services.admin_service import list_users
        admins_result = list_users(role='admin', limit=500, offset=0)
        admins_list = admins_result['data']['users'] if admins_result['success'] else []
        
        # Get unique actions and target tables for filter dropdowns
        from src.data_access.database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT action FROM admin_logs ORDER BY action")
            actions_list = [row['action'] for row in cursor.fetchall()]
            
            cursor.execute("SELECT DISTINCT target_table FROM admin_logs ORDER BY target_table")
            target_tables_list = [row['target_table'] for row in cursor.fetchall()]
        
        return render_template('admin/logs.html',
                             logs=logs,
                             page=page,
                             page_size=page_size,
                             total_pages=total_pages,
                             total=total,
                             admin_id_filter=admin_id,
                             action_filter=action,
                             target_table_filter=target_table,
                             admins_list=admins_list,
                             actions_list=actions_list,
                             target_tables_list=target_tables_list)
    else:
        return render_template('admin/logs.html', logs=[], page=1, page_size=50, total_pages=0, total=0,
                             admin_id_filter=None, action_filter=None, target_table_filter=None,
                             admins_list=[], actions_list=[], target_tables_list=[])

@admin_bp.route('/resources')
@login_required
@admin_required
def resources():
    """List all resources for admin management."""
    from src.data_access.database import get_db_connection
    
    page = request.args.get('page', 1, type=int)
    page_size = min(100, max(1, request.args.get('page_size', 25, type=int)))
    offset = (page - 1) * page_size
    
    # Get filter parameters
    status_filter = request.args.get('status', '').strip() or None
    category_filter = request.args.get('category', '').strip() or None
    featured_filter = request.args.get('featured', '').strip()
    featured = parse_bool_filter(featured_filter)
    keyword_filter = request.args.get('keyword', '').strip() or None
    location_filter = request.args.get('location', '').strip() or None
    owner_id_filter = request.args.get('owner_id', type=int)
    is_24_hours_filter = request.args.get('is_24_hours', '').strip()
    is_24_hours = parse_bool_filter(is_24_hours_filter)
    
    # Get sort parameters
    sort_by = request.args.get('sort_by', '').strip() or None
    sort_order = request.args.get('sort_order', 'desc').strip()
    
    # Get filter options for dropdowns
    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Get unique categories
        cursor.execute("SELECT DISTINCT category FROM resources ORDER BY category")
        categories_list = [row['category'] for row in cursor.fetchall()]
        
        # Get unique locations (limit to 50 most common)
        cursor.execute("SELECT DISTINCT location FROM resources ORDER BY location LIMIT 50")
        locations_list = [row['location'] for row in cursor.fetchall()]
    
    # Get list of users who own resources
    owners_result = list_users(limit=500, offset=0)
    owners_list = owners_result['data']['users'] if owners_result['success'] else []
    
    result = list_resources(
        status=status_filter,
        category=category_filter,
        owner_id=owner_id_filter,
        featured=featured,
        keyword=keyword_filter,
        location=location_filter,
        is_24_hours=is_24_hours,
        sort_by=sort_by,
        sort_order=sort_order,
        limit=page_size,
        offset=offset
    )
    
    if result['success']:
        resources_list = result['data']['resources']
        total = result['data']['total']
        total_pages = (total + page_size - 1) // page_size
        
        # Check which resources are owned by deleted users
        from src.data_access.database import get_db_connection
        with get_db_connection() as conn:
            cursor = conn.cursor()
            owner_ids = [r['owner_id'] for r in resources_list]
            owner_deleted_map = {}
            if owner_ids:
                placeholders = ','.join(['?'] * len(owner_ids))
                cursor.execute(f"""
                    SELECT user_id, deleted FROM users WHERE user_id IN ({placeholders})
                """, owner_ids)
                for row in cursor.fetchall():
                    owner_deleted_map[row['user_id']] = bool(row['deleted'])
        
        # Add deleted owner flag to each resource
        for resource in resources_list:
            resource['owner_is_deleted'] = owner_deleted_map.get(resource['owner_id'], False)
        
        return render_template('admin/resources.html',
                             resources=resources_list,
                             page=page,
                             total_pages=total_pages,
                             total=total,
                             status_filter=status_filter,
                             category_filter=category_filter,
                             featured_filter=featured_filter,
                             keyword_filter=keyword_filter,
                             location_filter=location_filter,
                             owner_id_filter=owner_id_filter,
                             is_24_hours_filter=is_24_hours_filter,
                             sort_by=sort_by,
                             sort_order=sort_order,
                             categories_list=categories_list,
                             locations_list=locations_list,
                             owners_list=owners_list)
    else:
        return render_template('admin/resources.html', 
                             resources=[], 
                             page=1, 
                             total_pages=0, 
                             total=0,
                             status_filter=status_filter,
                             category_filter=category_filter,
                             featured_filter=featured_filter,
                             keyword_filter=keyword_filter,
                             location_filter=location_filter,
                             owner_id_filter=owner_id_filter,
                             is_24_hours_filter=is_24_hours_filter,
                             sort_by=sort_by,
                             sort_order=sort_order,
                             categories_list=categories_list,
                             locations_list=locations_list,
                             owners_list=owners_list)

@admin_bp.route('/resources/<int:resource_id>/feature', methods=['POST'])
@login_required
@admin_required
def feature_resource(resource_id):
    """Feature a resource on the homepage."""
    result = update_resource(resource_id, featured=1)
    
    if result['success']:
        log_admin_action(current_user.user_id, 'feature_resource', 'resources', resource_id, 
                        'Resource featured on homepage')
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
        log_admin_action(current_user.user_id, 'unfeature_resource', 'resources', resource_id, 
                        'Resource removed from homepage')
        flash('Resource removed from homepage.', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('admin.resources'))

@admin_bp.route('/resources/<int:resource_id>/archive', methods=['POST'])
@login_required
@admin_required
def archive_resource(resource_id):
    """Archive a resource. Admins can archive any resource."""
    from src.services.resource_service import delete_resource
    
    result = delete_resource(resource_id)
    
    if result['success']:
        log_admin_action(current_user.user_id, 'archive_resource', 'resources', resource_id, 
                        'Resource archived')
        flash('Resource archived successfully.', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('admin.resources'))

@admin_bp.route('/resources/<int:resource_id>/unarchive', methods=['POST'])
@login_required
@admin_required
def unarchive_resource(resource_id):
    """Unarchive a resource. Admins can unarchive any resource."""
    result = update_resource(resource_id, status='published')
    
    if result['success']:
        log_admin_action(current_user.user_id, 'unarchive_resource', 'resources', resource_id, 
                        'Resource unarchived (set to published)')
        flash('Resource unarchived successfully.', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('admin.resources'))

@admin_bp.route('/resources/<int:resource_id>/reassign', methods=['GET', 'POST'])
@login_required
@admin_required
def reassign_resource(resource_id):
    """Reassign resource ownership to another user. Admin only."""
    if request.method == 'GET':
        # Get resource info and list of users for reassignment
        result = get_resource(resource_id)
        if not result['success']:
            flash(result['error'], 'error')
            return redirect(url_for('admin.resources'))
        
        resource = result['data']
        
        # Get list of active users (excluding deleted users)
        users_result = list_users(limit=500, offset=0)
        users_list = users_result['data']['users'] if users_result['success'] else []
        
        # Get current owner information
        from src.data_access.database import get_db_connection
        current_owner = None
        owner_is_deleted = False
        
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id, name, email, deleted FROM users WHERE user_id = ?", (resource['owner_id'],))
            owner_info = cursor.fetchone()
            
            if owner_info:
                owner_is_deleted = bool(owner_info['deleted'])
                current_owner = {
                    'user_id': owner_info['user_id'],
                    'name': owner_info['name'] if owner_info['name'] else '[Deleted User]',
                    'email': owner_info['email'] if owner_info['email'] else '[Deleted]',
                    'deleted': owner_is_deleted
                }
        
        return render_template('admin/reassign_resource.html',
                             resource=resource,
                             users=users_list,
                             owner_is_deleted=owner_is_deleted,
                             current_owner=current_owner)
    
    # POST request - perform reassignment
    new_owner_id = request.form.get('new_owner_id', type=int)
    
    if not new_owner_id:
        flash('Please select a new owner.', 'error')
        return redirect(url_for('admin.reassign_resource', resource_id=resource_id))
    
    result = reassign_resource_ownership(resource_id, new_owner_id, current_user.user_id)
    
    if result['success']:
        flash('Resource ownership reassigned successfully.', 'success')
        return redirect(url_for('admin.resources'))
    else:
        flash(result['error'], 'error')
        return redirect(url_for('admin.reassign_resource', resource_id=resource_id))

@admin_bp.route('/bookings')
@login_required
@admin_required
def bookings():
    """List all bookings for admin management."""
    from src.services.booking_service import list_bookings
    from src.services.resource_service import get_resource, list_resources
    from src.models.user import User
    
    status_filter = request.args.get('status', '').strip() or None
    resource_id = request.args.get('resource_id', type=int)
    user_id = request.args.get('user_id', type=int)
    section_filter = request.args.get('section')  # 'upcoming', 'previous', 'pending', 'in_progress', or None for all
    
    # Get all bookings (ignore pagination for sectioning, but limit to reasonable amount)
    result = list_bookings(user_id=user_id, resource_id=resource_id, status=status_filter, limit=1000, offset=0)
    
    if result['success']:
        all_bookings = result['data']['bookings']
        total = result['data']['total']
        
        # Categorize bookings
        categorized = categorize_bookings(all_bookings, section_filter)
        upcoming_bookings = categorized['upcoming']
        previous_bookings = categorized['previous']
        in_progress_bookings = categorized.get('in_progress', [])
        pending_bookings = categorized.get('pending', [])
        
        # Enrich with resource and user info
        for booking in upcoming_bookings + previous_bookings + in_progress_bookings + pending_bookings:
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
        
        # Get resources list for filter dropdown
        resources_result = list_resources(status=None, limit=500, offset=0)
        resources_list = resources_result['data']['resources'] if resources_result['success'] else []
        
        # Get users list for filter dropdown
        users_result = list_users(limit=500, offset=0)
        users_list = users_result['data']['users'] if users_result['success'] else []
        
        return render_template('admin/bookings.html',
                             upcoming_bookings=upcoming_bookings,
                             previous_bookings=previous_bookings,
                             in_progress_bookings=in_progress_bookings,
                             pending_bookings=pending_bookings,
                             total=total,
                             status_filter=status_filter,
                             resource_id_filter=resource_id,
                             user_id_filter=user_id,
                             section_filter=section_filter,
                             resources_list=resources_list,
                             users_list=users_list)
    else:
        return render_template('admin/bookings.html', 
                             upcoming_bookings=[],
                             previous_bookings=[],
                             in_progress_bookings=[],
                             pending_bookings=[],
                             total=0,
                             status_filter=status_filter,
                             resource_id_filter=resource_id,
                             user_id_filter=user_id,
                             section_filter=section_filter,
                             resources_list=[],
                             users_list=[])

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
        details = f"Booking updated by admin"
        if start_datetime or end_datetime:
            details += f" (datetime changed)"
        if status:
            details += f" (status: {status})"
        
        log_admin_action(current_user.user_id, 'update_booking', 'bookings', booking_id, details)
        
        flash('Booking updated successfully.', 'success')
    else:
        flash(result['error'], 'error')
    
    return redirect(url_for('admin.booking_detail', booking_id=booking_id))

@admin_bp.route('/bookings/<int:booking_id>/approve', methods=['POST'])
@login_required
@admin_required
def approve_booking_admin(booking_id):
    """Approve a pending booking request (admin only)."""
    result = get_booking(booking_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('admin.bookings'))
    
    booking = result['data']
    
    # Check if booking is pending
    if booking['status'] != 'pending':
        flash('This booking is not pending approval.', 'error')
        return redirect(url_for('admin.bookings'))
    
    # Get resource to check ownership
    resource_result = get_resource(booking['resource_id'])
    if not resource_result['success']:
        flash('Resource not found.', 'error')
        return redirect(url_for('admin.bookings'))
    
    resource = resource_result['data']
    
    # Check for conflicts before approving
    conflicts = check_conflicts(booking['resource_id'], booking['start_datetime'], booking['end_datetime'], exclude_booking_id=booking_id)
    if conflicts:
        flash('Cannot approve: This time slot conflicts with an existing approved booking.', 'error')
        return redirect(url_for('admin.bookings'))
    
    # Update booking status to approved
    update_result = update_booking_status(booking_id, 'approved')
    
    if update_result['success']:
        # Send automated message to message thread indicating admin approval
        from src.models.user import User
        from dateutil import parser
        from dateutil.tz import gettz
        est_tz = gettz('America/New_York')
        
        requester = User.get(booking['requester_id'])
        owner = User.get(resource['owner_id'])
        
        if requester:
            start_dt = parser.parse(booking['start_datetime'])
            end_dt = parser.parse(booking['end_datetime'])
            start_dt_est = start_dt.astimezone(est_tz)
            end_dt_est = end_dt.astimezone(est_tz)
            
            date_str = start_dt_est.strftime('%B %d, %Y')
            start_time_str = start_dt_est.strftime('%I:%M %p').lstrip('0')
            end_time_str = end_dt_est.strftime('%I:%M %p').lstrip('0')
            
            # Message to requester
            message_content = f"This booking was approved by an administrator.\n\nBooking Request for {resource['title']}\n\nRequester: {requester.name}\nDate: {date_str}\nTime: {start_time_str} - {end_time_str}\n\nYour booking is now confirmed."
            
            send_message(
                sender_id=current_user.user_id,
                receiver_id=booking['requester_id'],
                content=message_content,
                resource_id=booking['resource_id'],
                booking_id=booking_id
            )
            
            # Message to resource owner to notify them admin approved
            if owner and owner.user_id != current_user.user_id:
                owner_message = f"This booking was approved by an administrator.\n\nBooking Request for {resource['title']}\n\nRequester: {requester.name}\nDate: {date_str}\nTime: {start_time_str} - {end_time_str}\n\nBooking ID: {booking_id}\n\nThe booking has been approved and no further action is required."
                
                send_message(
                    sender_id=current_user.user_id,
                    receiver_id=resource['owner_id'],
                    content=owner_message,
                    resource_id=booking['resource_id'],
                    booking_id=booking_id
                )
        
        # Log admin action
        log_admin_action(current_user.user_id, 'approve_booking', 'bookings', booking_id, f"Approved booking request for resource {resource['title']}")
        
        flash('Booking request approved successfully!', 'success')
    else:
        flash(update_result.get('error', 'Error approving booking request.'), 'error')
    
    return redirect(url_for('admin.bookings'))

@admin_bp.route('/bookings/<int:booking_id>/deny', methods=['POST'])
@login_required
@admin_required
def deny_booking_admin(booking_id):
    """Deny a pending booking request (admin only)."""
    result = get_booking(booking_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('admin.bookings'))
    
    booking = result['data']
    
    # Check if booking is pending
    if booking['status'] != 'pending':
        flash('This booking is not pending approval.', 'error')
        return redirect(url_for('admin.bookings'))
    
    # Get resource to check ownership
    resource_result = get_resource(booking['resource_id'])
    if not resource_result['success']:
        flash('Resource not found.', 'error')
        return redirect(url_for('admin.bookings'))
    
    resource = resource_result['data']
    
    # Update booking status to denied
    update_result = update_booking_status(booking_id, 'denied')
    
    if update_result['success']:
        # Send notification message to requester
        from src.models.user import User
        from dateutil import parser
        from dateutil.tz import gettz
        est_tz = gettz('America/New_York')
        
        requester = User.get(booking['requester_id'])
        if requester:
            start_dt = parser.parse(booking['start_datetime'])
            end_dt = parser.parse(booking['end_datetime'])
            start_dt_est = start_dt.astimezone(est_tz)
            end_dt_est = end_dt.astimezone(est_tz)
            
            date_str = start_dt_est.strftime('%B %d, %Y')
            start_time_str = start_dt_est.strftime('%I:%M %p').lstrip('0')
            end_time_str = end_dt_est.strftime('%I:%M %p').lstrip('0')
            
            message_content = f"Your booking request for {resource['title']} has been denied by an administrator.\n\nDate: {date_str}\nTime: {start_time_str} - {end_time_str}\n\nIf you have questions, please contact the resource owner or administrator."
            
            send_message(
                sender_id=current_user.user_id,
                receiver_id=booking['requester_id'],
                content=message_content,
                resource_id=booking['resource_id'],
                booking_id=booking_id
            )
        
        # Log admin action
        log_admin_action(current_user.user_id, 'deny_booking', 'bookings', booking_id, f"Denied booking request for resource {resource['title']}")
        
        flash('Booking request denied successfully!', 'success')
    else:
        flash(update_result.get('error', 'Error denying booking request.'), 'error')
    
    return redirect(url_for('admin.bookings'))

