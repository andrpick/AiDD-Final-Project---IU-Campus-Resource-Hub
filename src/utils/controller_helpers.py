"""
Controller helper utilities for common patterns.
"""
from flask import flash, redirect, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from typing import List, Optional, Tuple, Callable, Any, Dict
import os
import uuid
from datetime import datetime
from dateutil.tz import tzutc
from src.utils.logging_config import get_logger
from src.utils.datetime_utils import parse_datetime_aware

logger = get_logger(__name__)

# Image upload constants
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_IMAGE_COUNT = 10  # Maximum images per resource


def check_resource_permission(resource_owner_id: int, error_message: str = 'Unauthorized.') -> Tuple[bool, Optional[Any]]:
    """
    Check if current user has permission to modify a resource.
    
    Args:
        resource_owner_id: ID of the resource owner
        error_message: Custom error message to flash
        
    Returns:
        Tuple of (has_permission: bool, error_response: Optional[redirect])
    """
    if not current_user.is_authenticated:
        flash('Please log in to access this page.', 'error')
        return False, redirect(url_for('auth.login'))
    
    if resource_owner_id != current_user.user_id and not current_user.is_admin():
        flash(error_message, 'error')
        return False, redirect(url_for('home'))
    
    return True, None


def handle_service_result(result: dict, success_message: str, 
                         success_redirect: Callable, 
                         error_redirect: Optional[Callable] = None) -> Any:
    """
    Handle service result and flash appropriate message.
    
    Args:
        result: Service result dictionary with 'success' and either 'data' or 'error'
        success_message: Message to flash on success
        success_redirect: Function to call for redirect on success (takes result['data'] as kwargs)
        error_redirect: Function to call for redirect on error (optional)
        
    Returns:
        Flask redirect response
    """
    if result['success']:
        flash(success_message, 'success')
        return success_redirect(**result['data'])
    else:
        flash(result['error'], 'error')
        if error_redirect:
            return error_redirect()
        return redirect(url_for('home'))


def allowed_image_file(filename: str) -> bool:
    """
    Check if file extension is allowed for image uploads.
    
    Args:
        filename: Name of the file
        
    Returns:
        True if file extension is allowed
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_uploaded_images(uploaded_files: List[FileStorage], upload_folder: str, 
                        subfolder: str = 'resources') -> List[str]:
    """
    Save uploaded image files and return list of relative paths.
    
    Args:
        uploaded_files: List of uploaded file objects
        upload_folder: Base upload folder path
        subfolder: Subfolder within upload folder (e.g., 'resources')
        
    Returns:
        List of relative file paths (e.g., ['resources/uuid.jpg', ...])
    """
    if not uploaded_files:
        return []
    
    image_paths = []
    resource_uploads = os.path.join(upload_folder, subfolder)
    os.makedirs(resource_uploads, exist_ok=True)
    
    for file in uploaded_files[:MAX_IMAGE_COUNT]:  # Limit number of images
        if file and file.filename != '' and allowed_image_file(file.filename):
            try:
                # Generate unique filename
                filename = secure_filename(file.filename)
                ext = filename.rsplit('.', 1)[1].lower()
                unique_filename = f"{uuid.uuid4().hex}.{ext}"
                
                # Save file
                file_path = os.path.join(resource_uploads, unique_filename)
                file.save(file_path)
                
                # Store relative path for database
                image_paths.append(f"{subfolder}/{unique_filename}")
                logger.debug(f"Saved image: {image_paths[-1]}")
            except Exception as e:
                logger.error(f"Error saving image {file.filename}: {e}", exc_info=True)
                # Continue with other files even if one fails
    
    return image_paths


def delete_image_file(image_path: str, upload_folder: str) -> bool:
    """
    Delete an image file from the server.
    
    Args:
        image_path: Relative path to image (e.g., 'resources/uuid.jpg')
        upload_folder: Base upload folder path
        
    Returns:
        True if file was deleted successfully, False otherwise
    """
    try:
        full_path = os.path.join(upload_folder, image_path)
        if os.path.exists(full_path):
            os.remove(full_path)
            logger.debug(f"Deleted image: {image_path}")
            return True
    except Exception as e:
        logger.error(f"Error deleting image {image_path}: {e}", exc_info=True)
    return False


def parse_existing_images(images_field: Optional[str]) -> List[str]:
    """
    Parse existing images JSON field into a list.
    
    Args:
        images_field: JSON string or list of image paths
        
    Returns:
        List of image paths
    """
    if not images_field:
        return []
    
    if isinstance(images_field, list):
        return images_field
    
    try:
        from src.utils.json_utils import safe_json_loads
        parsed = safe_json_loads(images_field)
        return parsed if isinstance(parsed, list) else []
    except Exception:
        return []


def combine_images(existing_images: List[str], new_images: List[str], 
                  removed_images: Optional[List[str]] = None) -> List[str]:
    """
    Combine existing and new images, removing specified images.
    
    Args:
        existing_images: List of existing image paths
        new_images: List of newly uploaded image paths
        removed_images: Optional list of image paths to remove
        
    Returns:
        Combined list of image paths
    """
    # Remove specified images
    if removed_images:
        existing_images = [img for img in existing_images if img not in removed_images]
    
    # Combine existing and new images
    return existing_images + new_images


def save_profile_image(uploaded_file: Optional[FileStorage], upload_folder: str) -> Optional[str]:
    """
    Save a single profile image and return relative path.
    
    Args:
        uploaded_file: Single uploaded file object (or None)
        upload_folder: Base upload folder path
        
    Returns:
        Relative path to saved image (e.g., 'profiles/uuid.jpg') or None if no file
    """
    if not uploaded_file or not uploaded_file.filename or uploaded_file.filename == '':
        return None
    
    if not allowed_image_file(uploaded_file.filename):
        logger.warning(f"Invalid file type for profile image: {uploaded_file.filename}")
        return None
    
    try:
        profile_uploads = os.path.join(upload_folder, 'profiles')
        os.makedirs(profile_uploads, exist_ok=True)
        
        # Generate unique filename
        filename = secure_filename(uploaded_file.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        unique_filename = f"{uuid.uuid4().hex}.{ext}"
        
        # Save file
        file_path = os.path.join(profile_uploads, unique_filename)
        uploaded_file.save(file_path)
        
        # Return relative path for database
        relative_path = f"profiles/{unique_filename}"
        logger.debug(f"Saved profile image: {relative_path}")
        return relative_path
    except Exception as e:
        logger.error(f"Error saving profile image {uploaded_file.filename}: {e}", exc_info=True)
        return None


def get_booking_display_status(booking: Dict) -> str:
    """
    Get the display status for a booking, including computed "in_progress" status.
    
    A booking is "in_progress" when:
    - Status is 'approved' AND
    - Current time is between start_datetime and end_datetime
    
    Args:
        booking: Dictionary with booking data (must have 'status', 'start_datetime', 'end_datetime')
    
    Returns:
        String status: 'in_progress', 'approved', 'cancelled', or 'completed'
    """
    status = booking.get('status', 'approved')
    
    # Only compute "in_progress" for approved bookings
    if status == 'approved':
        try:
            now = datetime.now(tzutc())
            start_dt = parse_datetime_aware(booking.get('start_datetime', ''))
            end_dt = parse_datetime_aware(booking.get('end_datetime', ''))
            
            # Check if current time is between start and end
            if start_dt <= now <= end_dt:
                return 'in_progress'
        except Exception:
            # If parsing fails, return original status
            pass
    
    return status

def categorize_bookings(bookings: List[Dict], section_filter: Optional[str] = None) -> Dict[str, List[Dict]]:
    """
    Categorize bookings into upcoming, in_progress, previous, and canceled groups.
    
    Args:
        bookings: List of booking dictionaries with 'start_datetime', 'end_datetime', and 'status' fields
        section_filter: Optional filter to return only one section ('upcoming', 'in_progress', 'previous', 'canceled')
        
    Returns:
        Dictionary with keys: 'upcoming', 'in_progress', 'previous', 'canceled', each containing a list of bookings
    """
    # Get current time in UTC
    now = datetime.now(tzutc())
    
    # Separate bookings into four categories
    upcoming_bookings = []  # Approved bookings that haven't started yet
    in_progress_bookings = []  # Approved bookings that are currently active
    previous_bookings = []  # Approved bookings that have ended OR completed bookings
    canceled_bookings = []  # Canceled bookings regardless of date
    
    for booking in bookings:
        try:
            # Parse booking datetimes
            start_dt = parse_datetime_aware(booking['start_datetime'])
            end_dt = parse_datetime_aware(booking['end_datetime'])
            
            if booking['status'] == 'cancelled':
                # Canceled bookings go to canceled section
                canceled_bookings.append(booking)
            elif booking['status'] == 'approved':
                # Check if booking is currently in progress
                if start_dt <= now <= end_dt:
                    # Currently active booking
                    in_progress_bookings.append(booking)
                elif start_dt > now:
                    # Upcoming approved bookings (haven't started yet)
                    upcoming_bookings.append(booking)
                else:
                    # Previous approved bookings (have ended)
                    previous_bookings.append(booking)
            elif booking['status'] == 'completed':
                # Completed bookings go to previous section
                previous_bookings.append(booking)
            else:
                # Any other status goes to previous section
                previous_bookings.append(booking)
        except Exception:
            # If parsing fails, treat as previous booking
            if booking['status'] == 'cancelled':
                canceled_bookings.append(booking)
            else:
                previous_bookings.append(booking)
    
    # Sort upcoming by start_datetime ASC (soonest first)
    upcoming_bookings.sort(key=lambda b: parse_datetime_aware(b['start_datetime']))
    
    # Sort in_progress by start_datetime ASC (started earliest first)
    in_progress_bookings.sort(key=lambda b: parse_datetime_aware(b['start_datetime']))
    
    # Sort previous by start_datetime DESC (most recent first)
    previous_bookings.sort(key=lambda b: parse_datetime_aware(b['start_datetime']), reverse=True)
    
    # Sort canceled by start_datetime DESC (most recent first)
    canceled_bookings.sort(key=lambda b: parse_datetime_aware(b['start_datetime']), reverse=True)
    
    # Apply section filter if specified
    if section_filter == 'upcoming':
        in_progress_bookings = []
        previous_bookings = []
        canceled_bookings = []
    elif section_filter == 'in_progress':
        upcoming_bookings = []
        previous_bookings = []
        canceled_bookings = []
    elif section_filter == 'previous':
        upcoming_bookings = []
        in_progress_bookings = []
        canceled_bookings = []
    elif section_filter == 'canceled':
        upcoming_bookings = []
        in_progress_bookings = []
        previous_bookings = []
    # If section_filter is None or 'all', show all sections
    
    return {
        'upcoming': upcoming_bookings,
        'in_progress': in_progress_bookings,
        'previous': previous_bookings,
        'canceled': canceled_bookings
    }


def handle_service_error(result: dict, error_redirect: Optional[Callable] = None, 
                        default_error_message: Optional[str] = None) -> Any:
    """
    Handle service error result and return appropriate redirect response.
    
    Args:
        result: Service result dictionary with 'success' and 'error' keys
        error_redirect: Optional function to call for redirect on error (takes no args)
        default_error_message: Optional default error message if result['error'] is empty
        
    Returns:
        Flask redirect response or None if result is successful
        
    Note:
        Call this function only when result['success'] is False.
        If result is successful, this function returns None.
    """
    if result.get('success'):
        return None
    
    error_message = result.get('error') or default_error_message or 'An error occurred.'
    flash(error_message, 'error')
    
    if error_redirect:
        return error_redirect()
    
    return redirect(url_for('home'))


def log_admin_action(admin_id: int, action: str, target_table: str, target_id: int, 
                    details: Optional[str] = None) -> None:
    """
    Log an admin action to the admin_logs table.
    
    Args:
        admin_id: ID of the admin user performing the action
        action: Action name (e.g., 'feature_resource', 'archive_resource')
        target_table: Table name being affected (e.g., 'resources', 'bookings')
        target_id: ID of the target record
        details: Optional details about the action
    """
    from src.data_access.database import get_db_connection
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO admin_logs (admin_id, action, target_table, target_id, details)
                VALUES (?, ?, ?, ?, ?)
            """, (admin_id, action, target_table, target_id, details))
            conn.commit()
            logger.debug(f"Logged admin action: {action} on {target_table}:{target_id} by admin:{admin_id}")
    except Exception as e:
        logger.error(f"Error logging admin action: {e}", exc_info=True)
        # Don't raise exception - logging failure shouldn't break the main operation


def parse_bool_filter(filter_value: str) -> Optional[bool]:
    """
    Parse a boolean filter parameter from request args.
    
    Args:
        filter_value: String value from request args (e.g., '1', '0', '' or None)
        
    Returns:
        True if filter_value is '1', False if '0', None otherwise
    """
    if not filter_value:
        return None
    filter_value = filter_value.strip()
    if filter_value == '1':
        return True
    elif filter_value == '0':
        return False
    return None
