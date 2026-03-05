"""
User domain events
"""
from ddd.shared.domain import DomainEvent
from ddd.user_management.domain.value_objects import Email, Role


class UserCreatedEvent(DomainEvent):
    
    def __init__(self, user_id: str, email: Email, role: Role, full_name: str = None):
        super().__init__()
        self.user_id = user_id
        self.email = email.value
        self.role = role.value.value
        self.full_name = full_name


class UserPasswordChangedEvent(DomainEvent):
    
    def __init__(self, user_id: str):
        super().__init__()
        self.user_id = user_id


class UserDeactivatedEvent(DomainEvent):
    
    def __init__(self, user_id: str):
        super().__init__()
        self.user_id = user_id


class UserActivatedEvent(DomainEvent):
        
    def __init__(self, user_id: str):
        super().__init__()
        self.user_id = user_id
