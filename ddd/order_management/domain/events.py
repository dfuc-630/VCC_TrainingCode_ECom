"""
Order domain events
"""
from decimal import Decimal
from ddd.shared.domain import DomainEvent


class OrderCreatedEvent(DomainEvent):
    def __init__(self, order_id: str, order_number: str, customer_id: str):
        super().__init__()
        self.order_id = order_id
        self.order_number = order_number
        self.customer_id = customer_id


class OrderConfirmedEvent(DomainEvent):
    def __init__(self, order_id: str, order_number: str, customer_id: str, seller_id: str, total_amount: Decimal):
        super().__init__()
        self.order_id = order_id
        self.order_number = order_number
        self.customer_id = customer_id
        self.seller_id = seller_id
        self.total_amount = float(total_amount)


class OrderShippedEvent(DomainEvent):
    def __init__(self, order_id: str):
        super().__init__()
        self.order_id = order_id


class OrderCompletedEvent(DomainEvent):
    def __init__(self, order_id: str):
        super().__init__()
        self.order_id = order_id


class OrderCancelledEvent(DomainEvent):
    def __init__(self, order_id: str, total_amount: 'Money' = None):
        super().__init__()
        self.order_id = order_id
        if total_amount:
            self.total_amount = float(total_amount.amount)


class OrderFailedEvent(DomainEvent):
    def __init__(self, order_id: str, error_message: str):
        super().__init__()
        self.order_id = order_id
        self.error_message = error_message
