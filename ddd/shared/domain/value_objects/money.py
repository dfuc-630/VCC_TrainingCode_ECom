"""
Money value object - represents monetary amounts
"""
from decimal import Decimal
from ddd.shared.domain.value_object import ValueObject
from ddd.shared.domain.exceptions import InvalidValueObjectError


class Money(ValueObject):
    
    def __init__(self, amount: Decimal | int | str, currency: str = "VND"):
        
        if isinstance(amount, (int, str)):
            amount = Decimal(str(amount))
        
        if amount < 0:
            raise InvalidValueObjectError("Amount cannot be negative")
        
        # Round to 2 decimal places (standard for currency)
        self._amount = Decimal(str(amount)).quantize(Decimal('0.01'))
        self._currency = currency
    
    @property
    def amount(self) -> Decimal:
        return self._amount
    
    @property
    def currency(self) -> str:
        return self._currency
    
    def add(self, other: 'Money') -> 'Money':
        
        if self._currency != other._currency:
            raise InvalidValueObjectError("Cannot add different currencies")
        return Money(self._amount + other._amount, self._currency)
    
    def subtract(self, other: 'Money') -> 'Money':

        if self._currency != other._currency:
            raise InvalidValueObjectError("Cannot subtract different currencies")
        result = self._amount - other._amount
        if result < 0:
            raise InvalidValueObjectError("Subtraction would result in negative amount")
        return Money(result, self._currency)
    
    def multiply(self, quantity: int) -> 'Money':
        
        if quantity < 0:
            raise InvalidValueObjectError("Quantity cannot be negative")
        return Money(self._amount * Decimal(quantity), self._currency)
    
    def is_zero(self) -> bool:
        return self._amount == 0
    
    def is_greater_than(self, other: 'Money') -> bool:
        
        if self._currency != other._currency:
            raise InvalidValueObjectError("Cannot compare different currencies")
        return self._amount > other._amount
    
    def is_less_than(self, other: 'Money') -> bool:
        
        if self._currency != other._currency:
            raise InvalidValueObjectError("Cannot compare different currencies")
        return self._amount < other._amount
    
    def __repr__(self) -> str:
        return f"{self._currency} {self._amount}"

    def __lt__(self, other: 'Money') -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self._currency != other._currency:
            raise InvalidValueObjectError("Cannot compare different currencies")
        return self._amount < other._amount

    def __le__(self, other: 'Money') -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self._currency != other._currency:
            raise InvalidValueObjectError("Cannot compare different currencies")
        return self._amount <= other._amount

    def __gt__(self, other: 'Money') -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self._currency != other._currency:
            raise InvalidValueObjectError("Cannot compare different currencies")
        return self._amount > other._amount

    def __ge__(self, other: 'Money') -> bool:
        if not isinstance(other, Money):
            return NotImplemented
        if self._currency != other._currency:
            raise InvalidValueObjectError("Cannot compare different currencies")
        return self._amount >= other._amount

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Money):
            return False
        return self._amount == other._amount and self._currency == other._currency