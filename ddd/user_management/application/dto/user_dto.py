from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from ddd.user_management.domain.entities.user import User

@dataclass
class UserDTO:
    """Data Transfer Object for User"""
    id: str
    email: str
    full_name: Optional[str]
    phone: Optional[str]
    role: str
    is_active: bool
    created_at: str
    updated_at: str
    
    @staticmethod
    def from_entity(user) -> 'UserDTO':
        """Convert User entity to DTO"""
        
        if not isinstance(user, User):
            return None
        
        return UserDTO(
            id=user.id,
            email=user.email.value,
            full_name=user.full_name,
            phone=user.phone.value if user.phone else None,
            role=str(user.role.value),
            is_active=user.is_active,
            created_at=user.created_at.isoformat(),
            updated_at=user.updated_at.isoformat(),
        )
    
    def to_dict(self):
        """Convert DTO to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'full_name': self.full_name,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at,
            'updated_at': self.updated_at,
        }


@dataclass
class CreateUserResponseDTO:
    """Response DTO after user creation"""
    user_id: str
    email: str
    message: str = "User created successfully"
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'email': self.email,
            'message': self.message,
        }
