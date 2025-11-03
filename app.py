"""
Flask application entry point for Indiana University Campus Resource Hub.
"""
from flask import Flask, render_template
from flask_login import LoginManager
import os
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from dateutil import parser
from dateutil.tz import gettz, tzutc

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, 
            template_folder='src/views',
            static_folder='src/static')

# Load configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DATABASE_PATH'] = os.environ.get('DATABASE_PATH', 'campus_resource_hub.db')
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'uploads/')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

# User loader for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    """Load user object for Flask-Login session management."""
    from src.models.user import User
    return User.get(user_id)

# Custom Jinja2 filters for date/time formatting
@app.template_filter('format_datetime_est')
def format_datetime_est(value, format_type='full'):
    """Format datetime to EST timezone with readable format."""
    if not value:
        return 'N/A'
    
    try:
        # Parse the datetime string using dateutil
        if isinstance(value, str):
            dt = parser.parse(value)
        elif isinstance(value, datetime):
            dt = value
        else:
            return str(value)
        
        # If datetime is naive, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tzutc())
        
        # Convert to EST/EDT (America/New_York handles DST automatically)
        est_tz = gettz('America/New_York')
        dt_est = dt.astimezone(est_tz)
        
        # Determine timezone abbreviation (EDT or EST)
        # Check if we're in daylight saving time (EDT) or standard time (EST)
        is_dst = bool(dt_est.dst() and dt_est.dst().total_seconds() != 0)
        tz_abbrev = 'EDT' if is_dst else 'EST'
        
        # Format based on type
        if format_type == 'date':
            return dt_est.strftime('%B %d, %Y')  # "November 03, 2025"
        elif format_type == 'time':
            return dt_est.strftime('%I:%M %p')  # "02:00 PM"
        elif format_type == 'datetime':
            return dt_est.strftime('%B %d, %Y at %I:%M %p') + ' ' + tz_abbrev  # "November 03, 2025 at 02:00 PM EST"
        elif format_type == 'short':
            return dt_est.strftime('%m/%d/%Y %I:%M %p') + ' ' + tz_abbrev  # "11/03/2025 02:00 PM EST"
        else:  # full
            return dt_est.strftime('%A, %B %d, %Y at %I:%M %p') + ' ' + tz_abbrev  # "Monday, November 03, 2025 at 02:00 PM EST"
    except Exception as e:
        # Return original value if parsing fails
        return str(value)

@app.template_filter('format_date_est')
def format_date_est(value):
    """Format date to EST timezone."""
    return format_datetime_est(value, format_type='date')

@app.template_filter('format_time_est')
def format_time_est(value):
    """Format time to EST timezone."""
    return format_datetime_est(value, format_type='time')

@app.template_filter('nl2br')
def nl2br(value):
    """Convert newlines to HTML <br> tags."""
    if value is None:
        return ''
    return str(value).replace('\n', '<br>')

@app.template_filter('format_category')
def format_category(value):
    """Format category name with proper capitalization. Handles special cases like 'AV'."""
    if not value:
        return ''
    
    # Replace underscores with spaces
    formatted = value.replace('_', ' ')
    
    # Split into words and capitalize each word
    words = formatted.split()
    formatted_words = []
    
    for word in words:
        # Keep "AV" as uppercase, otherwise title case
        if word.lower() == 'av':
            formatted_words.append('AV')
        else:
            formatted_words.append(word.capitalize())
    
    return ' '.join(formatted_words)

@app.template_filter('format_datetime_local')
def format_datetime_local(value):
    """Format datetime for HTML datetime-local input (YYYY-MM-DDTHH:mm)."""
    try:
        from dateutil import parser
        from dateutil.tz import tzutc, gettz
        
        if value is None:
            return ''
        
        # Parse the datetime
        if isinstance(value, str):
            dt = parser.parse(value)
        else:
            dt = value
        
        # If datetime is naive, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tzutc())
        
        # Convert to local timezone (EST/EDT)
        est_tz = gettz('America/New_York')
        dt_local = dt.astimezone(est_tz)
        
        # Format as YYYY-MM-DDTHH:mm for datetime-local input
        return dt_local.strftime('%Y-%m-%dT%H:%M')
    except Exception:
        return ''

# Import and register blueprints
from src.controllers.auth_controller import auth_bp
from src.controllers.resources_controller import resources_bp
from src.controllers.bookings_controller import bookings_bp
from src.controllers.search_controller import search_bp
from src.controllers.messages_controller import messages_bp
from src.controllers.reviews_controller import reviews_bp
from src.controllers.admin_controller import admin_bp
from src.controllers.ai_concierge_controller import ai_concierge_bp

app.register_blueprint(auth_bp)
app.register_blueprint(resources_bp)
app.register_blueprint(bookings_bp)
app.register_blueprint(search_bp)
app.register_blueprint(messages_bp)
app.register_blueprint(reviews_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(ai_concierge_bp)

# Context processor to make unread message count available in all templates
@app.context_processor
def inject_unread_count():
    """Inject unread message count into all templates."""
    from flask_login import current_user
    unread_count = 0
    if current_user.is_authenticated:
        from src.services.messaging_service import get_unread_count
        unread_count = get_unread_count(current_user.user_id)
    return {'unread_message_count': unread_count}

# Root route
@app.route('/')
def home():
    """Homepage."""
    from src.services.resource_service import get_featured_resources
    featured_result = get_featured_resources(limit=6)
    featured_resources = featured_result['data']['resources'] if featured_result['success'] else []
    return render_template('home.html', featured_resources=featured_resources)

# Create uploads directory on startup
if __name__ == '__main__':
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)

