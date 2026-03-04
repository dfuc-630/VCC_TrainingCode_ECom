"""
Order Item entity
"""
from datetime import datetime, timezone
from ddd.shared.domain import Entity
from ddd.shared.domain.value_objects import Money
from ddd.order_management.domain.value_objects import OrderItemStatus


class OrderItem(Entity):
    """
    Order item entity - child of Order aggregate.
    
    OrderItems cannot exist independently - they always belong to an Order.
    """
    
    def __init__(
        self,
        order_item_id: str,
        product_id: str,
        product_name: str,
        price: Money,
        quantity: int,
    ):
        super().__init__(order_item_id)
        self._product_id = product_id
        self._product_name = product_name
        self._price = price
        self._quantity = quantity
        self._subtotal = price.multiply(quantity)
        self._status = OrderItemStatus("pending")
        self._processing_at: datetime = None
    
    # Properties
    
    @property
    def product_id(self) -> str:
        return self._product_id
    
    @property
    def product_name(self) -> str:
        return self._product_name
    
    @property
    def price(self) -> Money:
        return self._price
    
    @property
    def quantity(self) -> int:
        return self._quantity
    
    @property
    def subtotal(self) -> Money:
        return self._subtotal
    
    @property
    def status(self) -> OrderItemStatus:
        return self._status
    
    @property
    def processing_at(self) -> datetime:
        return self._processing_at
    
    # Behavior
    
    def set_status(self, status: OrderItemStatus) -> None:
        """Update item status"""
        self._status = status
        self._processing_at = datetime.now(timezone.utc)
    
    def is_reserved(self) -> bool:
        return self._status.value == "reserved"
    
    def is_failed(self) -> bool:
        return self._status.value == "failed"
    
    def is_completed(self) -> bool:
        return self._status.value == "completed"
