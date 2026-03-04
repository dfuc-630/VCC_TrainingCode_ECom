"""
Password value object
"""
import bcrypt
from ddd.shared.domain.value_object import ValueObject
from ddd.shared.domain.exceptions import InvalidValueObjectError


class Password(ValueObject):
    """Type-safe password value object (hashed)"""
    
    MIN_LENGTH = 8
    
    def __init__(self, hashed_value: str):
        """
        Initialize Password with already hashed value (for loading from DB).
        Use Password.from_plain_text() for new passwords.
        """
        if not hashed_value or len(hashed_value) == 0:
            raise InvalidValueObjectError("Password hash cannot be empty")
        self._hashed_value = hashed_value
    
    @staticmethod
    def from_plain_text(plain_text: str) -> 'Password':
        """Create Password from plain text (hashes it)"""
        if not plain_text or len(plain_text) < Password.MIN_LENGTH:
            raise InvalidValueObjectError(
                f"Password must be at least {Password.MIN_LENGTH} characters"
            )
        
        hashed = bcrypt.hashpw(
            plain_text.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')
        
        return Password(hashed)
    
    def verify(self, plain_text: str) -> bool:
        """Verify a plain text password against this hash"""
        return bcrypt.checkpw(
            plain_text.encode('utf-8'),
            self._hashed_value.encode('utf-8')
        )
    
    @property
    def hashed_value(self) -> str:
        return self._hashed_value
    
    def __repr__(self) -> str:
        return "Password(***)"
