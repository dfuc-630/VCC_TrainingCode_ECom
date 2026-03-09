"""
Product catalog command classes
"""


class CreateProductCommand:
    """Command to create a new product"""
    
    def __init__(self, seller_id: str, name: str, description: str, 
                 price: float, quantity: int, category_id: str = None):
        self.seller_id = seller_id
        self.name = name
        self.description = description
        self.price = price
        self.quantity = quantity
        self.category_id = category_id


class UpdateProductCommand:
    """Command to update an existing product"""
    
    def __init__(self, product_id: str, seller_id: str, name: str = None,
                 description: str = None, price: float = None, quantity: int = None):
        self.product_id = product_id
        self.seller_id = seller_id
        self.name = name
        self.description = description
        self.price = price
        self.quantity = quantity


class ActivateProductCommand:
    """Command to activate a product"""
    
    def __init__(self, product_id: str, seller_id: str):
        self.product_id = product_id
        self.seller_id = seller_id


class DeactivateProductCommand:
    """Command to deactivate a product"""
    
    def __init__(self, product_id: str, seller_id: str):
        self.product_id = product_id
        self.seller_id = seller_id
