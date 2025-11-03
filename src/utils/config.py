"""
Centralized configuration management using environment variables.
"""
import os
from pathlib import Path


class Config:
    """Application configuration loaded from environment variables."""
    
    # Core Configuration (Required)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'campus_resource_hub.db')
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads/')
    
    # Flask Settings
    FLASK_DEBUG = os.environ.get('FLASK_DEBUG', '0') == '1'
    FLASK_HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.environ.get('FLASK_PORT', '5000'))
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_UPLOAD_SIZE', 16 * 1024 * 1024))  # 16MB default
    
    # Logging Configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.environ.get('LOG_DIR', 'logs/')
    
    # AI Concierge Configuration
    GOOGLE_GEMINI_API_KEY = os.environ.get('GOOGLE_GEMINI_API_KEY', '')
    ENABLE_AI_CONCIERGE = os.environ.get('ENABLE_AI_CONCIERGE', '1') == '1'
    
    # Booking System Configuration
    TIMEZONE = os.environ.get('TIMEZONE', 'America/New_York')
    BOOKING_OPERATING_HOURS_START = int(os.environ.get('BOOKING_OPERATING_HOURS_START', '8'))
    BOOKING_OPERATING_HOURS_END = int(os.environ.get('BOOKING_OPERATING_HOURS_END', '22'))
    BOOKING_MIN_ADVANCE_HOURS = int(os.environ.get('BOOKING_MIN_ADVANCE_HOURS', '1'))
    BOOKING_MIN_DURATION_MINUTES = int(os.environ.get('BOOKING_MIN_DURATION_MINUTES', '30'))
    BOOKING_MAX_DURATION_HOURS = int(os.environ.get('BOOKING_MAX_DURATION_HOURS', '8'))
    
    # Feature Flags
    ENABLE_REGISTRATION = os.environ.get('ENABLE_REGISTRATION', '1') == '1'
    
    # Production Settings
    PRODUCTION = os.environ.get('PRODUCTION', '0') == '1'
    
    @classmethod
    def validate(cls):
        """
        Validate required configuration values.
        Raises ValueError if required values are missing or invalid.
        """
        errors = []
        
        # Check SECRET_KEY in production
        if cls.PRODUCTION and cls.SECRET_KEY == 'dev-secret-key-change-in-production':
            errors.append("SECRET_KEY must be changed in production!")
        
        # Validate booking configuration
        if cls.BOOKING_OPERATING_HOURS_START < 0 or cls.BOOKING_OPERATING_HOURS_START > 23:
            errors.append("BOOKING_OPERATING_HOURS_START must be between 0 and 23")
        
        if cls.BOOKING_OPERATING_HOURS_END < 0 or cls.BOOKING_OPERATING_HOURS_END > 23:
            errors.append("BOOKING_OPERATING_HOURS_END must be between 0 and 23")
        
        if cls.BOOKING_OPERATING_HOURS_START >= cls.BOOKING_OPERATING_HOURS_END:
            errors.append("BOOKING_OPERATING_HOURS_START must be before BOOKING_OPERATING_HOURS_END")
        
        if cls.BOOKING_MIN_ADVANCE_HOURS < 0:
            errors.append("BOOKING_MIN_ADVANCE_HOURS must be >= 0")
        
        if cls.BOOKING_MIN_DURATION_MINUTES < 1:
            errors.append("BOOKING_MIN_DURATION_MINUTES must be >= 1")
        
        if cls.BOOKING_MAX_DURATION_HOURS < 1:
            errors.append("BOOKING_MAX_DURATION_HOURS must be >= 1")
        
        if cls.BOOKING_MIN_DURATION_MINUTES > cls.BOOKING_MAX_DURATION_HOURS * 60:
            errors.append("BOOKING_MIN_DURATION_MINUTES cannot exceed BOOKING_MAX_DURATION_HOURS")
        
        # Validate port
        if cls.FLASK_PORT < 1 or cls.FLASK_PORT > 65535:
            errors.append("FLASK_PORT must be between 1 and 65535")
        
        # Validate upload size
        if cls.MAX_CONTENT_LENGTH < 1024:  # At least 1KB
            errors.append("MAX_UPLOAD_SIZE must be at least 1024 bytes")
        
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
        
        return True
    
    @classmethod
    def get_summary(cls):
        """Get a summary of current configuration (safe for logging, excludes secrets)."""
        return {
            'database_path': cls.DATABASE_PATH,
            'upload_folder': cls.UPLOAD_FOLDER,
            'flask_debug': cls.FLASK_DEBUG,
            'flask_host': cls.FLASK_HOST,
            'flask_port': cls.FLASK_PORT,
            'max_upload_size_mb': cls.MAX_CONTENT_LENGTH / (1024 * 1024),
            'log_level': cls.LOG_LEVEL,
            'log_dir': cls.LOG_DIR,
            'timezone': cls.TIMEZONE,
            'booking_operating_hours': f"{cls.BOOKING_OPERATING_HOURS_START}:00 - {cls.BOOKING_OPERATING_HOURS_END}:00",
            'booking_min_advance_hours': cls.BOOKING_MIN_ADVANCE_HOURS,
            'booking_min_duration_minutes': cls.BOOKING_MIN_DURATION_MINUTES,
            'booking_max_duration_hours': cls.BOOKING_MAX_DURATION_HOURS,
            'enable_ai_concierge': cls.ENABLE_AI_CONCIERGE,
            'enable_registration': cls.ENABLE_REGISTRATION,
            'production': cls.PRODUCTION,
        }

