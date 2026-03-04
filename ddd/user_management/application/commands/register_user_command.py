from dataclasses import dataclass


@dataclass
class RegisterUserCommand:
    """Command to register a new user"""
    email: str
    password: str
    full_name: str
    phone: str = None
    role: str = "customer"


@dataclass
class ChangePasswordCommand:
    """Command to change user password"""
    user_id: str
    old_password: str
    new_password: str


@dataclass
class DeactivateUserCommand:
    """Command to deactivate a user account"""
    user_id: str


@dataclass
class ActivateUserCommand:
    """Command to activate a user account"""
    user_id: str


@dataclass
class UpdateUserProfileCommand:
    """Command to update user profile"""
    user_id: str
    full_name: str = None
    phone: str = None
