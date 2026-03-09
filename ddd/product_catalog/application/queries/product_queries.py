"""
Product query classes
"""


class GetProductQuery:
    """Query to get product details"""
    
    def __init__(self, product_id: str):
        self.product_id = product_id


class GetSellerProductsQuery:
    """Query to get all products from seller"""
    
    def __init__(self, seller_id: str, limit: int = 50, offset: int = 0, active_only: bool = True):
        self.seller_id = seller_id
        self.limit = limit
        self.offset = offset
        self.active_only = active_only


class SearchProductsQuery:
    """Query to search products"""
    
    def __init__(self, query: str = None, seller_id: str = None, 
                 active_only: bool = True, limit: int = 50, offset: int = 0):
        self.query = query
        self.seller_id = seller_id
        self.active_only = active_only
        self.limit = limit
        self.offset = offset
