"""
Authentication controller (Flask blueprint).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, send_from_directory
from flask_login import login_user, logout_user, login_required, current_user
from src.services.auth_service import register_user, authenticate_user
from src.services.admin_service import update_user
from src.models.user import User
from src.utils.controller_helpers import save_profile_image, delete_image_file

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        role = request.form.get('role', 'student').strip()
        department = request.form.get('department', '').strip() or None
        
        result = register_user(name, email, password, role, department)
        
        if result['success']:
            flash('Registration successful. Please log in.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(result['error'], 'error')
    
    return render_template('auth/register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login."""
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        result = authenticate_user(email, password)
        
        if result['success']:
            user = result['data']
            login_user(user)
            flash(f'Welcome back, {user.name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash(result['error'], 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout."""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

@auth_bp.route('/profile/<int:user_id>')
@login_required
def profile(user_id):
    """View user profile."""
    user = User.get(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('home'))
    
    # Only allow viewing own profile or admin
    if user_id != current_user.user_id and not current_user.is_admin():
        flash('Unauthorized.', 'error')
        return redirect(url_for('home'))
    
    return render_template('auth/profile.html', user=user)

@auth_bp.route('/profile/<int:user_id>/update', methods=['POST'])
@login_required
def update_profile(user_id):
    """Update user profile (allows users to update their own profile)."""
    # Only allow users to update their own profile (or admin can update any)
    if user_id != current_user.user_id and not current_user.is_admin():
        flash('Unauthorized. You can only update your own profile.', 'error')
        return redirect(url_for('auth.profile', user_id=user_id))
    
    user = User.get(user_id)
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('home'))
    
    if user.deleted:
        flash('Cannot update deleted user.', 'error')
        return redirect(url_for('home'))
    
    # Handle profile image upload
    profile_image_path = None
    if 'profile_image' in request.files:
        uploaded_file = request.files['profile_image']
        if uploaded_file and uploaded_file.filename:
            # Delete old profile image if exists
            if user.profile_image and user.profile_image.startswith('profiles/'):
                upload_folder = current_app.config['UPLOAD_FOLDER']
                delete_image_file(user.profile_image, upload_folder)
            
            # Save new profile image
            upload_folder = current_app.config['UPLOAD_FOLDER']
            profile_image_path = save_profile_image(uploaded_file, upload_folder)
            if not profile_image_path:
                flash('Failed to upload profile image. Please ensure it is a valid image file.', 'error')
                return redirect(url_for('auth.profile', user_id=user_id))
    
    # Only update if profile image was provided
    if profile_image_path is not None:
        # Update user via admin service (it handles admin_id checking)
        admin_id = current_user.user_id  # Users can update their own profile
        
        result = update_user(
            user_id=user_id,
            admin_id=admin_id,
            profile_image=profile_image_path
        )
        
        if result['success']:
            flash('Profile picture updated successfully.', 'success')
        else:
            flash(result.get('error', 'Failed to update profile picture.'), 'error')
    else:
        flash('Please upload a profile image file.', 'info')
    
    return redirect(url_for('auth.profile', user_id=user_id))

@auth_bp.route('/uploads/profiles/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded profile images."""
    import os
    upload_folder = current_app.config['UPLOAD_FOLDER']
    # filename is just the UUID part (e.g., 'uuid.jpg')
    # Use send_from_directory like resources route for consistency
    # First serve from uploads/profiles directory
    profile_folder = os.path.join(upload_folder, 'profiles')
    return send_from_directory(profile_folder, filename)

