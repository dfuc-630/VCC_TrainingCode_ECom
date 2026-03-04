"""
Notification domain - event-driven domain

This domain is purely event-driven and doesn't have entities.
It listens to domain events and sends notifications via Telegram, Email, etc.
"""
from ddd.shared.domain.base_entity import DomainEvent


class NotificationEvent(DomainEvent):
    """Base class for notification events"""
    
    def __init__(self, recipient: str, message: str, notification_type: str, **kwargs):
        super().__init__()
        self.recipient = recipient  # User ID, email, phone, etc.
        self.message = message
        self.notification_type = notification_type  # telegram, email, sms, etc.
        self.extra_data = kwargs


class OrderNotificationEvent(NotificationEvent):
    """Event for order notifications"""
    
    def __init__(self, order_id: str, recipient: str, message: str, **kwargs):
        super().__init__(recipient, message, "telegram", **kwargs)
        self.order_id = order_id


class UserNotificationEvent(NotificationEvent):
    """Event for user notifications"""
    
    def __init__(self, user_id: str, recipient: str, message: str, **kwargs):
        super().__init__(recipient, message, "telegram", **kwargs)
        self.user_id = user_id
