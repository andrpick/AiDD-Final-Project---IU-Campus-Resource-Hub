"""
Notification service for simulated email notifications.
Logs notifications instead of actually sending emails (acceptable per requirements).
"""
from src.utils.logging_config import get_logger
from datetime import datetime
from src.data_access.database import get_db_connection

logger = get_logger(__name__)

def send_booking_confirmation(booking_id, requester_email, resource_title, start_datetime, end_datetime):
    """
    Send booking confirmation notification.
    
    Args:
        booking_id: ID of the booking
        requester_email: Email of the person who made the booking
        resource_title: Title of the resource
        start_datetime: Start datetime of booking
        end_datetime: End datetime of booking
    """
    try:
        message = (
            f"Booking Confirmation\n"
            f"Booking ID: {booking_id}\n"
            f"Resource: {resource_title}\n"
            f"Start: {start_datetime}\n"
            f"End: {end_datetime}\n"
            f"Status: Confirmed\n\n"
            f"Your booking has been confirmed. You can view your booking details in your account."
        )
        
        logger.info(f"[NOTIFICATION] Booking Confirmation sent to {requester_email}")
        logger.info(f"[NOTIFICATION] Message: {message}")
        
        return {'success': True, 'message': 'Booking confirmation notification sent'}
    except Exception as e:
        logger.error(f"Error sending booking confirmation: {e}")
        return {'success': False, 'error': str(e)}

def send_booking_status_change(booking_id, requester_email, resource_title, old_status, new_status, reason=None):
    """
    Send notification when booking status changes.
    
    Args:
        booking_id: ID of the booking
        requester_email: Email of the person who made the booking
        resource_title: Title of the resource
        old_status: Previous status
        new_status: New status
        reason: Optional reason for status change
    """
    try:
        status_messages = {
            'approved': 'Your booking has been approved.',
            'cancelled': 'Your booking has been cancelled.',
            'completed': 'Your booking has been completed.',
            'denied': 'Your booking request has been denied.'
        }
        
        message = (
            f"Booking Status Update\n"
            f"Booking ID: {booking_id}\n"
            f"Resource: {resource_title}\n"
            f"Status Changed: {old_status} → {new_status}\n"
        )
        
        if new_status in status_messages:
            message += f"\n{status_messages[new_status]}"
        
        if reason:
            message += f"\nReason: {reason}"
        
        logger.info(f"[NOTIFICATION] Booking Status Change sent to {requester_email}")
        logger.info(f"[NOTIFICATION] Message: {message}")
        
        return {'success': True, 'message': 'Booking status change notification sent'}
    except Exception as e:
        logger.error(f"Error sending booking status change notification: {e}")
        return {'success': False, 'error': str(e)}

def send_booking_approval(booking_id, requester_email, resource_title, approver_name, start_datetime, end_datetime):
    """
    Send notification when booking is approved.
    
    Args:
        booking_id: ID of the booking
        requester_email: Email of the person who made the booking
        resource_title: Title of the resource
        approver_name: Name of person who approved
        start_datetime: Start datetime of booking
        end_datetime: End datetime of booking
    """
    try:
        message = (
            f"Booking Approved\n"
            f"Booking ID: {booking_id}\n"
            f"Resource: {resource_title}\n"
            f"Approved by: {approver_name}\n"
            f"Start: {start_datetime}\n"
            f"End: {end_datetime}\n\n"
            f"Your booking request has been approved. You can view your booking details in your account."
        )
        
        logger.info(f"[NOTIFICATION] Booking Approval sent to {requester_email}")
        logger.info(f"[NOTIFICATION] Message: {message}")
        
        return {'success': True, 'message': 'Booking approval notification sent'}
    except Exception as e:
        logger.error(f"Error sending booking approval notification: {e}")
        return {'success': False, 'error': str(e)}

def send_booking_rejection(booking_id, requester_email, resource_title, rejector_name, reason):
    """
    Send notification when booking is rejected.
    
    Args:
        booking_id: ID of the booking
        requester_email: Email of the person who made the booking
        resource_title: Title of the resource
        rejector_name: Name of person who rejected
        reason: Reason for rejection
    """
    try:
        message = (
            f"Booking Request Denied\n"
            f"Booking ID: {booking_id}\n"
            f"Resource: {resource_title}\n"
            f"Denied by: {rejector_name}\n"
            f"Reason: {reason}\n\n"
            f"Your booking request has been denied. Please contact the resource owner if you have questions."
        )
        
        logger.info(f"[NOTIFICATION] Booking Rejection sent to {requester_email}")
        logger.info(f"[NOTIFICATION] Message: {message}")
        
        return {'success': True, 'message': 'Booking rejection notification sent'}
    except Exception as e:
        logger.error(f"Error sending booking rejection notification: {e}")
        return {'success': False, 'error': str(e)}

