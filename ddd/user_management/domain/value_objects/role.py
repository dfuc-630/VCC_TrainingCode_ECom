"""
User role value object
"""
from enum import Enum
from ddd.shared.domain.value_object import ValueObject
from ddd.shared.domain.exceptions import InvalidValueObjectError


class UserRole(str, Enum):
    """Available user roles"""
    CUSTOMER = "customer"
    SELLER = "seller"
    ADMIN = "admin"


class Role(ValueObject):
    """Type-safe role value object"""
    
    def __init__(self, value: str):
        if not isinstance(value, str):
            raise InvalidValueObjectError("Role must be a string")
        
        try:
            self._role = UserRole(value.lower())
        except ValueError:
            valid_roles = ", ".join([r.value for r in UserRole])
            raise InvalidValueObjectError(f"Invalid role. Valid roles: {valid_roles}")
    
    @property
    def value(self) -> UserRole:
        return self._role
    
    def is_admin(self) -> bool:
        return self._role == UserRole.ADMIN
    
    def is_seller(self) -> bool:
        return self._role == UserRole.SELLER
    
    def is_customer(self) -> bool:
        return self._role == UserRole.CUSTOMER
    
    def __str__(self) -> str:
        return self._role.value
