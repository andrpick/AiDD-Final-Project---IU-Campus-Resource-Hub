"""
HTML utility functions for sanitization and escaping.
"""
import html
import re
from src.utils.logging_config import get_logger

logger = get_logger(__name__)


def sanitize_html(text, escape_html=False):
    """
    Remove HTML tags. Optionally escape HTML characters for titles/locations.
    
    Args:
        text: Text to sanitize
        escape_html: If True, escape HTML characters (for titles/locations)
    
    Returns:
        Sanitized text
    """
    if not text:
        return text
    
    # Simple HTML tag removal
    text = re.sub(r'<[^>]+>', '', text)
    
    # Only escape HTML characters if requested (for titles/locations, not descriptions)
    if escape_html:
        return html.escape(text)
    
    return text


def unescape_description(description):
    """
    Unescape HTML entities in description (handles legacy data that was escaped).
    
    Args:
        description: Description text to unescape
    
    Returns:
        Unescaped description or original if unescaping fails
    """
    if not description:
        return description
    
    try:
        return html.unescape(description)
    except (ValueError, TypeError) as e:
        logger.warning(f"Failed to unescape description: {e}")
        return description  # Return original if unescaping fails

