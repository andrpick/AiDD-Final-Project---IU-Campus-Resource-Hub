"""
Datetime utility functions.
"""
from datetime import datetime
from dateutil import parser
from dateutil.tz import gettz, tzutc
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def parse_datetime_aware(dt_str):
    """
    Parse datetime string and ensure it's timezone-aware (UTC).
    
    Args:
        dt_str: Datetime string (ISO format)
    
    Returns:
        timezone-aware datetime object in UTC
    """
    try:
        dt = parser.parse(dt_str.replace('Z', '+00:00'))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=tzutc())
        else:
            dt = dt.astimezone(tzutc())
        return dt
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to parse datetime string '{dt_str}': {e}")
        # Return a very old datetime as fallback for sorting
        return datetime(1970, 1, 1, tzinfo=tzutc())


def ensure_utc(dt):
    """
    Ensure datetime is timezone-aware in UTC.
    
    Args:
        dt: datetime object (may be naive or timezone-aware)
    
    Returns:
        timezone-aware datetime in UTC
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=tzutc())
    return dt.astimezone(tzutc())


def convert_to_est(dt):
    """
    Convert datetime to EST/EDT timezone.
    
    Args:
        dt: datetime object (timezone-aware or naive)
    
    Returns:
        datetime object in EST/EDT
    """
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tzutc())
    est_tz = gettz('America/New_York')
    return dt.astimezone(est_tz)


def format_datetime_est(value, format_type='full'):
    """
    Format datetime to EST timezone with readable format.
    
    Args:
        value: datetime string or datetime object
        format_type: 'full', 'date', 'time', 'datetime', or 'short'
    
    Returns:
        Formatted datetime string
    """
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
        is_dst = bool(dt_est.dst() and dt_est.dst().total_seconds() != 0)
        tz_abbrev = 'EDT' if is_dst else 'EST'
        
        # Format based on type
        if format_type == 'date':
            return dt_est.strftime('%B %d, %Y')  # "November 03, 2025"
        elif format_type == 'time':
            return dt_est.strftime('%I:%M %p')  # "02:00 PM"
        elif format_type == 'datetime':
            return dt_est.strftime('%B %d, %Y at %I:%M %p') + ' ' + tz_abbrev
        elif format_type == 'short':
            return dt_est.strftime('%m/%d/%Y %I:%M %p') + ' ' + tz_abbrev
        else:  # full
            return dt_est.strftime('%A, %B %d, %Y at %I:%M %p') + ' ' + tz_abbrev
    except (ValueError, TypeError, AttributeError) as e:
        logger.warning(f"Failed to format datetime '{value}': {e}")
        # Return original value if parsing fails
        return str(value)


def format_datetime_local(value):
    """
    Format datetime for HTML datetime-local input (YYYY-MM-DDTHH:mm).
    
    Args:
        value: datetime string or datetime object
    
    Returns:
        Formatted datetime string for HTML input
    """
    try:
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
    except (ValueError, TypeError, AttributeError) as e:
        logger.warning(f"Failed to format datetime for HTML input '{value}': {e}")
        return ''

