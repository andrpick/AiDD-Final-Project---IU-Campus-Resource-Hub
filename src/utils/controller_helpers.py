"""
Controller helper utilities for common patterns.
"""
from flask import flash, redirect, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from typing import List, Optional, Tuple, Callable, Any
import os
import uuid
from src.utils.logging_config import get_logger

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

