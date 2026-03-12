from typing import List, Optional
from ddd.order_management.application.queries.get_order_query import (
    GetOrderQuery,
    GetCustomerOrdersQuery,
    GetSellerOrdersQuery,
    ListPendingOrdersQuery,
)
from ddd.order_management.application.dto.order_dto import OrderDTO


class GetOrderQueryHandler:
    """Handler for retrieving order details"""
    
    def __init__(self, order_repository):
        self.order_repository = order_repository
    
    def execute(self, query: GetOrderQuery) -> Optional[OrderDTO]:
        """Get order by ID"""
        print(f"Executing GetOrderQueryHandler for order_id={query.order_id}")
        order = self.order_repository.find_by_id(query.order_id)
        
        if not order:
            return None
        
        return OrderDTO.from_entity(order)


class GetCustomerOrdersQueryHandler:
    """Handler for retrieving customer orders"""
    
    def __init__(self, order_repository):
        self.order_repository = order_repository
    
    def execute(self, query: GetCustomerOrdersQuery) -> List[OrderDTO]:
        """Get all orders for customer"""
        orders = self.order_repository.find_by_customer_id(
            query.customer_id,
            status=query.status,
        )
        
        return [OrderDTO.from_entity(order) for order in orders]


class GetSellerOrdersQueryHandler:
    """Handler for retrieving seller orders"""
    
    def __init__(self, order_repository):
        self.order_repository = order_repository
    
    def execute(self, query: GetSellerOrdersQuery) -> List[OrderDTO]:
        """Get all orders for seller"""
        orders = self.order_repository.find_by_seller_id(
            query.seller_id,
            status=query.status,
        )
        
        return [OrderDTO.from_entity(order) for order in orders]


class ListPendingOrdersQueryHandler:
    """Handler for retrieving pending orders"""
    
    def __init__(self, order_repository):
        self.order_repository = order_repository
    
    def execute(self, query: ListPendingOrdersQuery) -> List[OrderDTO]:
        """Get all pending orders"""
        orders = self.order_repository.find_pending_orders()
        
        return [OrderDTO.from_entity(order) for order in orders]
