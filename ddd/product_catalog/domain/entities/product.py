from uuid import uuid4
from datetime import datetime, timezone
from ddd.shared.domain.base_entity import AggregateRoot
from ddd.shared.domain.value_objects.money import Money


class Product(AggregateRoot):
    
    def __init__(self, product_id: str, seller_id: str, name: str, description: str, price: Money, 
        quantity: int, is_active: bool = True, created_at: datetime = None, updated_at: datetime = None,):
        
        super().__init__(product_id)
        self.seller_id = seller_id
        self.name = name
        self.description = description
        self.price = price
        self.quantity = quantity
        self.is_active = is_active
    
    @staticmethod
    def create(seller_id: str, name: str, description: str, price: Money, quantity: int,) -> 'Product':
        product = Product(
            product_id=str(uuid4()),
            seller_id=seller_id,
            name=name,
            description=description,
            price=price,
            quantity=quantity,
        )
        return product
    
    def decrease_quantity(self, amount: int) -> bool:
        if self.quantity < amount:
            return False
        self.quantity -= amount
        return True
    
    def increase_quantity(self, amount: int):
        self.quantity += amount
    
    def deactivate(self):
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)
    
    def activate(self):
        self.is_active = True
        self.updated_at = datetime.now(timezone.utc)
