"""
Custom exception classes for the Campus Resource Hub application.
"""
from typing import Optional, Dict, Any


class CampusResourceHubError(Exception):
    """Base exception for all Campus Resource Hub errors."""
    pass


class ValidationError(CampusResourceHubError):
    """Raised when input validation fails."""
    pass


class NotFoundError(CampusResourceHubError):
    """Raised when a requested resource is not found."""
    pass


class ConflictError(CampusResourceHubError):
    """Raised when a booking conflict is detected."""
    def __init__(self, message: str, conflicts: Optional[list] = None):
        super().__init__(message)
        self.conflicts = conflicts or []


class AuthorizationError(CampusResourceHubError):
    """Raised when a user lacks required permissions."""
    pass


class DatabaseError(CampusResourceHubError):
    """Raised when a database operation fails."""
    pass


class BookingError(CampusResourceHubError):
    """Raised when a booking operation fails."""
    pass


class ResourceError(CampusResourceHubError):
    """Raised when a resource operation fails."""
    pass


class AuthenticationError(CampusResourceHubError):
    """Raised when authentication fails."""
    pass

