"""
Utility functions for the Campus Resource Hub application.
"""
from .datetime_utils import (
    parse_datetime_aware,
    ensure_utc,
    convert_to_est,
    format_datetime_est,
    format_datetime_local
)
from .json_utils import (
    safe_json_loads,
    safe_json_dumps,
    parse_resource_json_fields
)
from .html_utils import (
    sanitize_html,
    unescape_description
)
from .config import Config
from .logging_config import get_logger, setup_logging
from .exceptions import (
    CampusResourceHubError,
    ValidationError,
    NotFoundError,
    ConflictError,
    AuthorizationError,
    DatabaseError,
    BookingError,
    ResourceError,
    AuthenticationError
)
from .decorators import admin_required, owner_or_admin_required
from .controller_helpers import (
    check_resource_permission,
    handle_service_result,
    allowed_image_file,
    save_uploaded_images,
    delete_image_file,
    parse_existing_images,
    combine_images,
    categorize_bookings,
    handle_service_error,
    log_admin_action,
    parse_bool_filter
)
from .query_builder import QueryBuilder

__all__ = [
    # Datetime utilities
    'parse_datetime_aware',
    'ensure_utc',
    'convert_to_est',
    'format_datetime_est',
    'format_datetime_local',
    # JSON utilities
    'safe_json_loads',
    'safe_json_dumps',
    'parse_resource_json_fields',
    # HTML utilities
    'sanitize_html',
    'unescape_description',
    # Configuration
    'Config',
    # Logging
    'get_logger',
    'setup_logging',
    # Exceptions
    'CampusResourceHubError',
    'ValidationError',
    'NotFoundError',
    'ConflictError',
    'AuthorizationError',
    'DatabaseError',
    'BookingError',
    'ResourceError',
    'AuthenticationError',
    # Decorators
    'admin_required',
    'owner_or_admin_required',
    # Controller helpers
    'check_resource_permission',
    'handle_service_result',
    'allowed_image_file',
    'save_uploaded_images',
    'delete_image_file',
    'parse_existing_images',
    'combine_images',
    'categorize_bookings',
    'handle_service_error',
    'log_admin_action',
    'parse_bool_filter',
    # Query builder
    'QueryBuilder',
]

