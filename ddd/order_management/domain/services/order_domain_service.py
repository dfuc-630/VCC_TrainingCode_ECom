"""
Order domain service
"""
from ddd.order_management.domain.entities import Order
from ddd.order_management.domain.value_objects import OrderStatus
from ddd.order_management.domain.exceptions import InvalidOrderStatusTransitionError


class OrderDomainService:
    """
    Order domain service for complex business rules.
    
    Encapsulates logic that doesn't belong to a single entity.
    """
    
    @staticmethod
    def can_transition_status(current_status: OrderStatus, new_status: OrderStatus) -> bool:
        """
        Determine if order status transition is valid.
        
        Business rules:
        - pending -> confirmed, cancelled
        - confirmed -> shipping, cancelled  
        - shipping -> completed
        """
        return current_status.can_transition_to(new_status)
    
    @staticmethod
    def validate_order_for_payment(order: Order) -> None:
        """
        Validate if order is ready for payment.
        
        Raises:
            InvalidOrderStatusTransitionError: If order status is not confirmed
        """
        if order.status.value != "confirmed":
            raise InvalidOrderStatusTransitionError(
                f"Order must be confirmed before payment. Current status: {order.status.value}"
            )
        
        if not order.is_all_items_reserved():
            raise InvalidOrderStatusTransitionError(
                "Not all items are reserved"
            )
