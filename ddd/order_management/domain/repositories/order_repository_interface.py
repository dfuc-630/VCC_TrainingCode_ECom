"""
Order repository interface
"""
from abc import abstractmethod
from typing import Optional, List

from ddd.shared.infrastructure import Repository
from ddd.order_management.domain.entities import Order
from ddd.order_management.domain.value_objects import OrderStatus


class OrderRepository(Repository[Order]):
    """
    Order repository interface.
    
    Defines contract for order persistence and queries.
    """
    
    @abstractmethod
    def find_by_order_number(self, order_number: str) -> Optional[Order]:
        """Find order by order number"""
        pass
    
    @abstractmethod
    def find_by_customer_id(self, customer_id: str, status: Optional[str] = None) -> List[Order]:
        """Find orders by customer ID, optionally filtered by status"""
        pass
    
    @abstractmethod
    def find_by_seller_id(self, seller_id: str, status: Optional[str] = None) -> List[Order]:
        """Find orders by seller ID, optionally filtered by status"""
        pass
    
    @abstractmethod
    def find_by_status(self, status: str) -> List[Order]:
        """Find all orders with specific status"""
        pass
    
    @abstractmethod
    def find_pending_orders(self) -> List[Order]:
        """Find all pending orders"""
        pass
