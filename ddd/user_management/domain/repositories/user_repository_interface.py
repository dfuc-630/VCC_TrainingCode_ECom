"""
User repository interface
"""
from abc import abstractmethod
from typing import Optional

from ddd.shared.infrastructure import Repository
from ddd.user_management.domain.entities import User
from ddd.user_management.domain.value_objects import Email


class UserRepository(Repository[User]):
    """
    User repository interface.
    
    This interface defines the contract for user persistence.
    Concrete implementations can use different storage backends (SQL, NoSQL, etc.).
    """
    
    @abstractmethod
    def find_by_email(self, email: Email) -> Optional[User]:
        """
        Find user by email.
        
        Args:
            email: User email value object
            
        Returns:
            User if found, None otherwise
        """
        pass
    
    @abstractmethod
    def find_by_username(self, username: str) -> Optional[User]:
        """Find user by username"""
        pass
    
    @abstractmethod
    def email_exists(self, email: Email) -> bool:
        """Check if email already exists"""
        pass
    
    @abstractmethod
    def username_exists(self, username: str) -> bool:
        """Check if username already exists"""
        pass
