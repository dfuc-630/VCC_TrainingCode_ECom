"""
Rich User aggregate root
"""
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from ddd.shared.domain import AggregateRoot
from ddd.user_management.domain.value_objects import Email, Password, PhoneNumber, Role, UserRole
from ddd.user_management.domain.events import (
    UserCreatedEvent,
    UserPasswordChangedEvent,
    UserDeactivatedEvent,
    UserActivatedEvent,
)
from ddd.user_management.domain.exceptions import (
    UserAlreadyDeactivatedError,
    CannotLoginError,
)

class User(AggregateRoot):
    
    def __init__(self, user_id: str, email: Email, password: Password, role: Role, 
                full_name: Optional[str] = None, phone: Optional[PhoneNumber] = None,):

        super().__init__(user_id)
        self._email = email
        self._password = password
        self._role = role
        self._full_name = full_name
        self._phone = phone
        self._is_active = True
        self._deleted_at: Optional[datetime] = None
    
    @staticmethod
    def create(email: Email, password_plain: str, role: Role, full_name: Optional[str] = None,
               phone: Optional[PhoneNumber] = None,) -> 'User':
    
        user_id = str(uuid4())
        password_hash = Password.from_plain_text(password_plain)
        
        user = User(
            user_id=user_id,
            email=email,
            password=password_hash,
            role=role,
            full_name=full_name,
            phone=phone,
        )
        
        # Raise event to notify other domains
        user.raise_domain_event(UserCreatedEvent(user_id, email, role, full_name))
        
        return user
    
    # Properties (read-only)
    
    @property
    def email(self) -> Email:
        return self._email
    
    @property
    def role(self) -> Role:
        return self._role
    
    @property
    def full_name(self) -> Optional[str]:
        return self._full_name
    
    @property
    def phone(self) -> Optional[PhoneNumber]:
        return self._phone
    
    @property
    def is_active(self) -> bool:
        return self._is_active and self._deleted_at is None
    
    @property
    def is_deleted(self) -> bool:
        return self._deleted_at is not None
    
    @property
    def deleted_at(self) -> Optional[datetime]:
        return self._deleted_at
    
    # Behavior methods (business logic)
    
    def verify_password(self, plain_password: str) -> bool:
        """Verify a plain text password against stored hash"""
        return self._password.verify(plain_password)
    
    def change_password(self, old_password_plain: str, new_password_plain: str) -> None:
        """
        Change user password.
        
        Validates old password before changing.
        
        Args:
            old_password_plain: Current password in plain text
            new_password_plain: New password in plain text
            
        Raises:
            InvalidPasswordError: If old password is incorrect
        """
        if not self.verify_password(old_password_plain):
            from ddd.user_management.domain.exceptions import InvalidPasswordError
            raise InvalidPasswordError("Current password is incorrect")
        
        self._password = Password.from_plain_text(new_password_plain)
        self.raise_domain_event(UserPasswordChangedEvent(self.id))
    
    def update_profile(self, full_name: Optional[str] = None, phone: Optional[PhoneNumber] = None,) -> None:
        """Update user profile information"""
        if full_name is not None:
            self._full_name = full_name
        if phone is not None:
            self._phone = phone
        self._updated_at = datetime.now(timezone.utc)
    
    def deactivate(self) -> None:
        """
        Deactivate user account.
        
        Raises:
            UserAlreadyDeactivatedError: If user is already deactivated
        """
        if not self.is_active:
            raise UserAlreadyDeactivatedError("User is already deactivated")
        
        self._is_active = False
        self.raise_domain_event(UserDeactivatedEvent(self.id))
    
    def activate(self) -> None:
        """Activate user account"""
        if self.is_active:
            return
        
        self._is_active = True
        self.raise_domain_event(UserActivatedEvent(self.id))
    
    def soft_delete(self) -> None:
        """Mark user as deleted (soft delete)"""
        self._deleted_at = datetime.now(timezone.utc)
    
    def restore(self) -> None:
        """Restore soft-deleted user"""
        self._deleted_at = None
    
    def can_login(self) -> bool:
        """Check if user can login"""
        return self.is_active and not self.is_deleted
    
    def assert_can_login(self) -> None:
        """
        Assert user can login, raise exception if not.
        
        Raises:
            CannotLoginError: If user cannot login
        """
        if not self.can_login():
            if not self._is_active:
                raise CannotLoginError("User account is deactivated")
            if self.is_deleted:
                raise CannotLoginError("User account is deleted")
            raise CannotLoginError("User cannot login")
    
    def is_admin(self) -> bool:
        """Check if user is admin"""
        return self._role.is_admin()
    
    def is_seller(self) -> bool:
        """Check if user is seller"""
        return self._role.is_seller()
    
    def is_customer(self) -> bool:
        """Check if user is customer"""
        return self._role.is_customer()
    
    def has_role(self, role: Role) -> bool:
        """Check if user has specific role"""
        return self._role == role
    
    def __repr__(self) -> str:
        return f"User(id={self.id}, email={self._email}, role={self._role}, active={self.is_active})"
