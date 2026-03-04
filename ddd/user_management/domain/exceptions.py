"""
User domain exceptions
"""
from ddd.shared.domain.exceptions import DomainException


class UserException(DomainException):
    """Base exception for user domain"""
    pass


class InvalidEmailError(UserException):
    """Raised when email is invalid"""
    pass


class InvalidPasswordError(UserException):
    """Raised when password is invalid"""
    pass


class UserNotFoundError(UserException):
    """Raised when user is not found"""
    pass


class UserAlreadyExistsError(UserException):
    """Raised when trying to create a user with existing email"""
    pass


class UserAlreadyDeactivatedError(UserException):
    """Raised when trying to deactivate already deactivated user"""
    pass


class CannotLoginError(UserException):
    """Raised when user cannot login"""
    pass
