"""
Email value object
"""
import re
from ddd.shared.domain.value_object import ValueObject
from ddd.shared.domain.exceptions import InvalidValueObjectError


class Email(ValueObject):
    """Type-safe email value object"""
    
    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    
    def __init__(self, value: str):
        if not value or not isinstance(value, str):
            raise InvalidValueObjectError("Email must be a non-empty string")
        
        value = value.strip().lower()
        
        if not self.EMAIL_REGEX.match(value):
            raise InvalidValueObjectError(f"Invalid email format: {value}")
        
        if len(value) > 255:
            raise InvalidValueObjectError("Email is too long")
        
        self._value = value
    
    @property
    def value(self) -> str:
        return self._value
    
    def __str__(self) -> str:
        return self._value
    
    def __repr__(self) -> str:
        return f"Email({self._value})"
