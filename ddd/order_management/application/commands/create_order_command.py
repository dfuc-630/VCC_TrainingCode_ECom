"""
Create order command
"""
from dataclasses import dataclass
from typing import List


@dataclass
class CreateOrderItemCommand:
    """Command data for order item"""
    product_id: str
    quantity: int


@dataclass
class CreateOrderCommand:
    """Command to create a new order"""
    customer_id: str
    seller_id: str
    items: List[CreateOrderItemCommand]
    shipping_address: str
    shipping_phone: str


@dataclass
class CancelOrderCommand:
    """Command to cancel an order"""
    order_id: str
    customer_id: str


@dataclass
class ConfirmOrderCommand:
    """Command to confirm an order"""
    order_id: str


@dataclass
class ShipOrderCommand:
    """Command to ship an order"""
    order_id: str
    seller_id: str


@dataclass
class CompleteOrderCommand:
    """Command to mark order as completed"""
    order_id: str
