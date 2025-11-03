"""
JSON utility functions for safe parsing and serialization.
"""
import json
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def safe_json_loads(json_str, default=None):
    """
    Safely parse JSON string with error handling.
    
    Args:
        json_str: JSON string to parse
        default: Default value to return if parsing fails
    
    Returns:
        Parsed JSON object or default value
    """
    if not json_str:
        return default
    
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON: {e}")
        return default


def safe_json_dumps(obj, default=None):
    """
    Safely serialize object to JSON string.
    
    Args:
        obj: Object to serialize
        default: Default value to return if serialization fails
    
    Returns:
        JSON string or default value
    """
    if obj is None:
        return default
    
    try:
        return json.dumps(obj)
    except (TypeError, ValueError) as e:
        logger.warning(f"Failed to serialize to JSON: {e}")
        return default


def parse_resource_json_fields(resource):
    """
    Parse JSON fields in a resource dictionary.
    
    Args:
        resource: Resource dictionary from database
    
    Returns:
        Resource dictionary with parsed JSON fields
    """
    # Parse images JSON
    if resource.get('images'):
        resource['images'] = safe_json_loads(resource['images'], default=[])
    else:
        resource['images'] = []
    
    # Parse availability_rules JSON
    if resource.get('availability_rules'):
        resource['availability_rules'] = safe_json_loads(resource['availability_rules'], default=None)
    
    return resource

