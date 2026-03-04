"""
Order Management - Value Objects
"""
from enum import Enum
from ddd.shared.domain.value_object import ValueObject
from ddd.shared.domain.exceptions import InvalidValueObjectError


class OrderStatus(str, Enum):
    """Order status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPING = "shipping"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class OrderStatus(ValueObject):
    """Type-safe order status value object"""
    
    VALID_STATUSES = {
        "pending", "confirmed", "shipping", "completed", "cancelled", "failed"
    }
    
    VALID_TRANSITIONS = {
        "pending": {"confirmed", "cancelled"},
        "confirmed": {"shipping", "cancelled"},
        "shipping": {"completed"},
    }
    
    def __init__(self, value: str):
        if value not in self.VALID_STATUSES:
            raise InvalidValueObjectError(f"Invalid order status: {value}")
        self._value = value
    
    @property
    def value(self) -> str:
        return self._value
    
    def can_transition_to(self, new_status: 'OrderStatus') -> bool:
        """Check if transition is valid"""
        return new_status.value in self.VALID_TRANSITIONS.get(self._value, set())
    
    def __str__(self) -> str:
        return self._value


class OrderItemStatus(ValueObject):
    """Order item status value object"""
    
    VALID_STATUSES = {"pending", "reserved", "failed", "completed", "cancelled"}
    
    def __init__(self, value: str):
        if value not in self.VALID_STATUSES:
            raise InvalidValueObjectError(f"Invalid order item status: {value}")
        self._value = value
    
    @property
    def value(self) -> str:
        return self._value


class OrderId(ValueObject):
    """Type-safe order ID value object"""
    
    def __init__(self, value: str):
        if not value:
            raise InvalidValueObjectError("Order ID cannot be empty")
        self._value = value
    
    @property
    def value(self) -> str:
        return self._value
    
    @staticmethod
    def generate() -> 'OrderId':
        from uuid import uuid4
        return OrderId(str(uuid4()))
    
    def __str__(self) -> str:
        return self._value


class OrderNumber(ValueObject):
    """Order number value object"""
    
    def __init__(self, value: str):
        if not value:
            raise InvalidValueObjectError("Order number cannot be empty")
        self._value = value
    
    @property
    def value(self) -> str:
        return self._value
    
    @staticmethod
    def generate() -> 'OrderNumber':
        from datetime import datetime
        import random
        timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S')
        random_part = ''.join(str(random.randint(0, 9)) for _ in range(6))
        return OrderNumber(f"ORD-{timestamp}{random_part}")


class PaymentStatus(ValueObject):
    """Payment status value object"""
    
    VALID_STATUSES = {"unpaid", "paid", "refunded"}
    
    def __init__(self, value: str):
        if value not in self.VALID_STATUSES:
            raise InvalidValueObjectError(f"Invalid payment status: {value}")
        self._value = value
    
    @property
    def value(self) -> str:
        return self._value
