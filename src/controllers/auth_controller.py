"""
Authentication controller (Flask blueprint).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from src.services.auth_service import register_user, authenticate_user
from src.models.user import User

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

