"""
Login User Command
Used for user authentication
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class LoginUserCommand:
    """Command to login a user"""
    email: str
    password: str


@dataclass  
class LoginUserResult:
    """Result of login operation"""
    user_id: str
    email: str
    full_name: Optional[str]
    role: str
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'message': 'Login successful'
        }
