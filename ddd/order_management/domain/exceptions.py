"""
Order domain exceptions
"""
from ddd.shared.domain.exceptions import DomainException


class OrderException(DomainException):
    """Base exception for order domain"""
    pass


class CannotConfirmEmptyOrderError(OrderException):
    """Raised when trying to confirm order with no items"""
    pass


class CannotCancelOrderError(OrderException):
    """Raised when order cannot be cancelled"""
    pass


class CannotModifyCompletedOrderError(OrderException):
    """Raised when trying to modify completed order"""
    pass


class InvalidOrderStatusTransitionError(OrderException):
    """Raised when order status transition is invalid"""
    pass


class InsufficientStockError(OrderException):
    """Raised when product stock is insufficient"""
    pass


class InsufficientBalanceError(OrderException):
    """Raised when customer has insufficient balance"""
    pass


class OrderNotFoundError(OrderException):
    """Raised when order is not found"""
    pass


class InvalidOrderItemError(OrderException):
    """Raised when order item is invalid"""
    pass
