"""
Resources controller (Flask blueprint).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, current_app
from flask_login import login_required, current_user
from src.services.resource_service import create_resource, get_resource, update_resource, delete_resource, list_resources
from src.services.review_service import get_resource_reviews
from src.services.booking_service import list_bookings
from src.services.calendar_service import prepare_calendar_data
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
    
    # Get month and day from query parameters (default to current month)
    from datetime import date
    today = date.today()
    selected_year = request.args.get('year', today.year, type=int)
    selected_month = request.args.get('month', today.month, type=int)
    selected_day = request.args.get('day', type=int)  # Optional - if provided, show day view
    
    # Fetch approved bookings for the resource schedule
    approved_bookings_result = list_bookings(resource_id=resource_id, status='approved', limit=500, offset=0)
    
    all_bookings_raw = []
    if approved_bookings_result['success']:
        all_bookings_raw.extend(approved_bookings_result['data']['bookings'])
    
    # Prepare calendar data using service
    calendar_info = prepare_calendar_data(
        resource_id=resource_id,
        approved_bookings_raw=all_bookings_raw,
        selected_year=selected_year,
        selected_month=selected_month,
        selected_day=selected_day
    )
    
    calendar_data = calendar_info['calendar_data']
    day_data = calendar_info['day_data']
    booked_slots = calendar_info['booked_slots']
    approved_bookings = calendar_info['approved_bookings']
    prev_year = calendar_info['prev_year']
    prev_month = calendar_info['prev_month']
    next_year = calendar_info['next_year']
    next_month = calendar_info['next_month']
    can_go_prev = calendar_info['can_go_prev']
    current_time_info = calendar_info['current_time_info']
    
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
    """Edit a resource. Owners can edit their own resources, admins can edit any resource."""
    result = get_resource(resource_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('search.index'))
    
    resource = result['data']
    
    # Permission check: Owners can edit their own resources, admins can edit any resource
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
        
        # Owners can archive their own resources, admins can archive any resource
        if status == 'archived' and resource['owner_id'] != current_user.user_id and not current_user.is_admin():
            flash('Only resource owners and administrators can archive resources.', 'error')
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
    """Publish a draft resource. Owners can publish their own resources, admins can publish any resource."""
    result = get_resource(resource_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('search.index'))
    
    resource = result['data']
    
    # Permission check: Owners can publish their own resources, admins can publish any resource
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

@resources_bp.route('/<int:resource_id>/archive', methods=['POST'])
@login_required
def archive(resource_id):
    """Archive a resource. Owners can archive their own resources, admins can archive any resource."""
    result = get_resource(resource_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('search.index'))
    
    resource = result['data']
    
    # Permission check: Owners can archive their own resources, admins can archive any resource
    if resource['owner_id'] != current_user.user_id and not current_user.is_admin():
        flash('Only resource owners and administrators can archive resources.', 'error')
        return redirect(url_for('resources.detail', resource_id=resource_id))
    
    result = delete_resource(resource_id)
    
    if result['success']:
        flash('Resource archived successfully.', 'success')
        return redirect(url_for('resources.detail', resource_id=resource_id))
    else:
        flash(result['error'], 'error')
        return redirect(url_for('resources.detail', resource_id=resource_id))

@resources_bp.route('/<int:resource_id>/unarchive', methods=['POST'])
@login_required
def unarchive(resource_id):
    """Unarchive a resource. Owners can unarchive their own resources, admins can unarchive any resource."""
    result = get_resource(resource_id)
    
    if not result['success']:
        flash(result['error'], 'error')
        return redirect(url_for('search.index'))
    
    resource = result['data']
    
    # Permission check: Owners can unarchive their own resources, admins can unarchive any resource
    if resource['owner_id'] != current_user.user_id and not current_user.is_admin():
        flash('Only resource owners and administrators can unarchive resources.', 'error')
        return redirect(url_for('resources.detail', resource_id=resource_id))
    
    if resource['status'] != 'archived':
        flash('Resource is not archived.', 'error')
        return redirect(url_for('resources.detail', resource_id=resource_id))
    
    result = update_resource(resource_id, status='published')
    
    if result['success']:
        flash('Resource unarchived successfully.', 'success')
        return redirect(url_for('resources.detail', resource_id=resource_id))
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

