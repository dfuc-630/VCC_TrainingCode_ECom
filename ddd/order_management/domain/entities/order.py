"""
Order aggregate root
"""
from datetime import datetime, timezone
from typing import List, Optional
from uuid import uuid4

from ddd.shared.domain import AggregateRoot
from ddd.shared.domain.value_objects import Money
from ddd.order_management.domain.value_objects import (
    OrderStatus,
    OrderItemStatus,
    OrderId,
    OrderNumber,
    PaymentStatus,
)
from ddd.order_management.domain.entities.order_item import OrderItem


class Order(AggregateRoot):
    """
    Order aggregate root.
    
    The Order aggregate manages:
    - Order state and business rules
    - Collection of OrderItems
    - Order lifecycle (pending -> confirmed -> shipping -> completed)
    
    Order is the only entry point to manage order items.
    """
    
    def __init__(self, order_id: str, order_number: str, customer_id: str, seller_id: str,
        shipping_address: str, shipping_phone: str,):

        super().__init__(order_id)
        self._order_number = order_number
        self._customer_id = customer_id
        self._seller_id = seller_id
        self._items: List[OrderItem] = []
        self._status = OrderStatus("pending")
        self._payment_status = PaymentStatus("unpaid")
        self._total_amount: Optional[Money] = None
        self._shipping_address = shipping_address
        self._shipping_phone = shipping_phone
        self._processing_at: Optional[datetime] = None
        self._retry_count = 0
        self._last_error: Optional[str] = None
        self._sent_tele = False
    
    @staticmethod
    def create(customer_id: str, seller_id: str, shipping_address: str, shipping_phone: str,) -> 'Order':
        """Factory method to create new order"""
        order_id = str(uuid4())
        order_number = OrderNumber.generate().value
        
        order = Order(
            order_id=order_id,
            order_number=order_number,
            customer_id=customer_id,
            seller_id=seller_id,
            shipping_address=shipping_address,
            shipping_phone=shipping_phone,
        )
        
        return order
    
    # Properties (read-only)
    
    @property
    def order_number(self) -> str:
        return self._order_number
    
    @property
    def customer_id(self) -> str:
        return self._customer_id
    
    @property
    def seller_id(self) -> str:
        return self._seller_id
    
    @property
    def items(self) -> List[OrderItem]:
        return self._items.copy()
    
    @property
    def status(self) -> OrderStatus:
        return self._status
    
    @property
    def payment_status(self) -> PaymentStatus:
        return self._payment_status
    
    @property
    def total_amount(self) -> Optional[Money]:
        return self._total_amount
    
    @property
    def shipping_address(self) -> str:
        return self._shipping_address
    
    @property
    def shipping_phone(self) -> str:
        return self._shipping_phone
    
    @property
    def retry_count(self) -> int:
        return self._retry_count
    
    @property
    def last_error(self) -> Optional[str]:
        return self._last_error
    
    # Behavior - items management
    
    def add_item(self, product_id: str, product_name: str, price: Money, quantity: int) -> OrderItem:
        """
        Add item to order.
        
        Raises:
            CannotModifyCompletedOrderError: If order is completed
        """
        if not self._can_modify():
            from ddd.order_management.domain.exceptions import CannotModifyCompletedOrderError
            raise CannotModifyCompletedOrderError()
        
        item = OrderItem(
            order_item_id=str(uuid4()),
            product_id=product_id,
            product_name=product_name,
            price=price,
            quantity=quantity,
        )
        
        self._items.append(item)
        self._update_total()
        
        return item
    
    def get_item(self, product_id: str) -> Optional[OrderItem]:
        """Get item by product ID"""
        for item in self._items:
            if item.product_id == product_id:
                return item
        return None
    
    def remove_item(self, product_id: str) -> None:
        """
        Remove item from order.
        
        Raises:
            CannotModifyCompletedOrderError: If order is completed
        """
        if not self._can_modify():
            from ddd.order_management.domain.exceptions import CannotModifyCompletedOrderError
            raise CannotModifyCompletedOrderError()
        
        self._items = [item for item in self._items if item.product_id != product_id]
        self._update_total()
    
    # Behavior - status transitions
    
    def confirm(self) -> None:
        """
        Confirm the order.
        
        Raises:
            CannotConfirmEmptyOrderError: If no items
            InvalidOrderStatusTransitionError: If invalid status transition
        """
        if len(self._items) == 0:
            from ddd.order_management.domain.exceptions import CannotConfirmEmptyOrderError
            raise CannotConfirmEmptyOrderError("Cannot confirm order with no items")
        
        if not self._status.can_transition_to(OrderStatus("confirmed")):
            from ddd.order_management.domain.exceptions import InvalidOrderStatusTransitionError
            raise InvalidOrderStatusTransitionError(
                f"Cannot transition from {self._status.value} to confirmed"
            )
        
        self._status = OrderStatus("confirmed")
        self._processing_at = datetime.now(timezone.utc)
        
        from ddd.order_management.domain.events import OrderConfirmedEvent
        self.raise_domain_event(OrderConfirmedEvent(
            order_id=self.id,
            order_number=self._order_number,
            customer_id=self._customer_id,
            seller_id=self._seller_id,
            total_amount=self._total_amount.amount,
        ))
    
    def ship(self) -> None:
        """Mark order as shipped"""
        if not self._status.can_transition_to(OrderStatus("shipping")):
            from ddd.order_management.domain.exceptions import InvalidOrderStatusTransitionError
            raise InvalidOrderStatusTransitionError()
        
        self._status = OrderStatus("shipping")
        
        from ddd.order_management.domain.events import OrderShippedEvent
        self.raise_domain_event(OrderShippedEvent(self.id))
    
    def complete(self) -> None:
        """Mark order as completed"""
        if self._status.value != "shipping":
            from ddd.order_management.domain.exceptions import InvalidOrderStatusTransitionError
            raise InvalidOrderStatusTransitionError()
        
        self._status = OrderStatus("completed")
        self._payment_status = PaymentStatus("paid")
        
        from ddd.order_management.domain.events import OrderCompletedEvent
        self.raise_domain_event(OrderCompletedEvent(self.id))
    
    def cancel(self) -> None:
        """
        Cancel the order.
        
        Raises:
            CannotCancelOrderError: If order cannot be cancelled
        """
        if not self._can_cancel():
            from ddd.order_management.domain.exceptions import CannotCancelOrderError
            raise CannotCancelOrderError(f"Cannot cancel order in {self._status.value} status")
        
        self._status = OrderStatus("cancelled")
        
        from ddd.order_management.domain.events import OrderCancelledEvent
        self.raise_domain_event(OrderCancelledEvent(self.id, self._total_amount))
    
    def fail(self, error_message: str) -> None:
        """Mark order as failed"""
        self._status = OrderStatus("failed")
        self._last_error = error_message
        self._retry_count += 1
        
        from ddd.order_management.domain.events import OrderFailedEvent
        self.raise_domain_event(OrderFailedEvent(self.id, error_message))
    
    # Query methods
    
    def can_cancel(self) -> bool:
        """Check if order can be cancelled"""
        return self._can_cancel()
    
    def _can_cancel(self) -> bool:
        return self._status.value in {"pending", "confirmed"}
    
    def _can_modify(self) -> bool:
        return self._status.value == "pending"
    
    def _update_total(self) -> None:
        """Calculate order total from items"""
        if len(self._items) == 0:
            self._total_amount = Money(0)
        else:
            total = Money(0)
            for item in self._items:
                total = total.add(item.subtotal)
            self._total_amount = total
    
    def get_all_items_with_status(self, status: str) -> List[OrderItem]:
        """Get items filtered by status"""
        return [item for item in self._items if item.status.value == status]
    
    def is_all_items_reserved(self) -> bool:
        """Check if all items are reserved"""
        if len(self._items) == 0:
            return False
        return all(item.is_reserved() for item in self._items)
    
    def is_any_item_failed(self) -> bool:
        """Check if any item failed"""
        return any(item.is_failed() for item in self._items)
