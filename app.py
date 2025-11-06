"""
Flask application entry point for Indiana University Campus Resource Hub.
"""
from flask import Flask, render_template
from flask_login import LoginManager
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables FIRST, before importing Config
# This ensures environment variables are available when Config class is evaluated
load_dotenv()

from src.utils.datetime_utils import format_datetime_est, format_datetime_local
from src.utils.logging_config import setup_logging
from src.utils.config import Config

# Set up logging
setup_logging()

# Validate configuration
try:
    Config.validate()
except ValueError as e:
    import sys
    print(f"ERROR: {e}", file=sys.stderr)
    sys.exit(1)

# Initialize Flask app
app = Flask(__name__, 
            template_folder='src/views',
            static_folder='src/static')

# Load configuration from Config class
app.config['SECRET_KEY'] = Config.SECRET_KEY
app.config['DATABASE_PATH'] = Config.DATABASE_PATH
app.config['UPLOAD_FOLDER'] = Config.UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = Config.MAX_CONTENT_LENGTH

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
def format_datetime_est_filter(value, format_type='full'):
    """Format datetime to EST timezone with readable format."""
    return format_datetime_est(value, format_type)

@app.template_filter('format_date_est')
def format_date_est_filter(value):
    """Format date to EST timezone."""
    return format_datetime_est(value, format_type='date')

@app.template_filter('format_time_est')
def format_time_est_filter(value):
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
def format_datetime_local_filter(value):
    """Format datetime for HTML datetime-local input (YYYY-MM-DDTHH:mm)."""
    return format_datetime_local(value)

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
    import os
    from src.utils.logging_config import get_logger
    logger = get_logger(__name__)
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Log configuration summary
    logger.info("Starting Campus Resource Hub application")
    config_summary = Config.get_summary()
    for key, value in config_summary.items():
        logger.info(f"  {key}: {value}")
    
    if Config.PRODUCTION:
        logger.warning("Running in PRODUCTION mode")
        if Config.FLASK_DEBUG:
            logger.error("WARNING: FLASK_DEBUG is enabled in production! This is a security risk!")
    
    app.run(debug=Config.FLASK_DEBUG, host=Config.FLASK_HOST, port=Config.FLASK_PORT)

