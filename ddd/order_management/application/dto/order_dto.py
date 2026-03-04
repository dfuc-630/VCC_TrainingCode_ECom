"""
Order DTOs
"""
from dataclasses import dataclass
from typing import List, Optional
from ddd.order_management.domain.entities import Order, OrderItem


@dataclass
class OrderItemDTO:
    """DTO for order item"""
    order_item_id: str
    product_id: str
    product_name: str
    price: float
    quantity: int
    subtotal: float
    status: str
    
    @staticmethod
    def from_entity(item: OrderItem) -> 'OrderItemDTO':
        return OrderItemDTO(
            order_item_id=item.id,
            product_id=item.product_id,
            product_name=item.product_name,
            price=float(item.price.amount),
            quantity=item.quantity,
            subtotal=float(item.subtotal.amount),
            status=item.status.value,
        )


@dataclass
class CreateOrderDTO:
    """DTO for create order response"""
    order_id: str
    order_number: str
    customer_id: str
    seller_id: str
    total_amount: float
    status: str
    items: List[OrderItemDTO]
    
    @staticmethod
    def from_entity(order: Order) -> 'CreateOrderDTO':
        return CreateOrderDTO(
            order_id=order.id,
            order_number=order.order_number,
            customer_id=order.customer_id,
            seller_id=order.seller_id,
            total_amount=float(order.total_amount.amount) if order.total_amount else 0,
            status=order.status.value,
            items=[OrderItemDTO.from_entity(item) for item in order.items],
        )


@dataclass
class OrderDTO:
    """DTO for order"""
    order_id: str
    order_number: str
    customer_id: str
    seller_id: str
    total_amount: float
    status: str
    payment_status: str
    shipping_address: str
    shipping_phone: str
    items: List[OrderItemDTO]
    created_at: str
    
    @staticmethod
    def from_entity(order: Order) -> 'OrderDTO':
        return OrderDTO(
            order_id=order.id,
            order_number=order.order_number,
            customer_id=order.customer_id,
            seller_id=order.seller_id,
            total_amount=float(order.total_amount.amount) if order.total_amount else 0,
            status=order.status.value,
            payment_status=order.payment_status.value,
            shipping_address=order.shipping_address,
            shipping_phone=order.shipping_phone,
            items=[OrderItemDTO.from_entity(item) for item in order.items],
            created_at=order.created_at.isoformat(),
        )
