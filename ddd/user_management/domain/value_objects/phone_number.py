"""
Phone number value object
"""
import re
from ddd.shared.domain.value_object import ValueObject
from ddd.shared.domain.exceptions import InvalidValueObjectError


class PhoneNumber(ValueObject):
    """Type-safe phone number value object"""
    
    # Vietnam phone number format
    PHONE_REGEX = re.compile(r'^(?:\+84|84|0)[1-9]\d{8}$')
    
    def __init__(self, value: str):
        if not value or not isinstance(value, str):
            raise InvalidValueObjectError("Phone number must be a non-empty string")
        
        # Remove spaces and dashes
        value = value.replace(' ', '').replace('-', '')
        
        if not self.PHONE_REGEX.match(value):
            raise InvalidValueObjectError(f"Invalid phone number format: {value}")
        
        self._value = value
    
    @property
    def value(self) -> str:
        return self._value
    
    def __str__(self) -> str:
        return self._value
