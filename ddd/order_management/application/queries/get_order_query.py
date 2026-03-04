from dataclasses import dataclass


@dataclass
class GetOrderQuery:
    """Query to get order details"""
    order_id: str


@dataclass
class GetCustomerOrdersQuery:
    """Query to list customer orders"""
    customer_id: str
    status: str = None


@dataclass
class GetSellerOrdersQuery:
    """Query to list seller orders"""
    seller_id: str
    status: str = None


@dataclass
class ListPendingOrdersQuery:
    """Query to list all pending orders"""
    pass
