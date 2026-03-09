"""
Product query handlers
"""
import logging

logger = logging.getLogger(__name__)


class GetProductQueryHandler:
    """Handler for getting product details"""
    
    def __init__(self, product_repository):
        self.product_repository = product_repository
    
    def execute(self, query):
        """
        Execute get product query
        
        Args:
            query: GetProductQuery
            
        Returns:
            dict with product info
        """
        logger.info(f"Fetching product: {query.product_id}")
        
        product = self.product_repository.find_by_id(query.product_id)
        if not product:
            raise Exception(f"Product not found: {query.product_id}")
        
        return {
            'id': product.id,
            'seller_id': product.seller_id,
            'name': product.name,
            'description': product.description,
            'price': product.price.amount,
            'quantity': product.quantity,
            'is_active': product.is_active,
        }


class GetSellerProductsQueryHandler:
    """Handler for getting seller's products"""
    
    def __init__(self, product_repository):
        self.product_repository = product_repository
    
    def execute(self, query):
        """
        Execute get seller products query
        
        Args:
            query: GetSellerProductsQuery
            
        Returns:
            list of product dicts
        """
        logger.info(f"Fetching products for seller: {query.seller_id}")
        
        products = self.product_repository.find_by_seller_id(query.seller_id)
        
        if query.active_only:
            products = [p for p in products if p.is_active]
        
        products = products[query.offset:query.offset + query.limit]
        
        return [{
            'id': p.id,
            'name': p.name,
            'price': p.price.amount,
            'quantity': p.quantity,
            'is_active': p.is_active,
        } for p in products]


class SearchProductsQueryHandler:
    """Handler for searching products"""
    
    def __init__(self, product_repository):
        self.product_repository = product_repository
    
    def execute(self, query):
        """
        Execute search products query
        
        Args:
            query: SearchProductsQuery
            
        Returns:
            list of matching product dicts
        """
        logger.info(f"Searching products: q='{query.query}'")
        
        # Get all active products (or all products if not filtering)
        all_products = self.product_repository.find_active(skip=0, limit=1000)
        
        # Filter by search query
        if query.query:
            search_query = query.query.lower()
            all_products = [
                p for p in all_products
                if search_query in p.name.lower() or search_query in p.description.lower()
            ]
        
        # Filter by seller
        if query.seller_id:
            all_products = [p for p in all_products if p.seller_id == query.seller_id]
        
        # Apply pagination
        products = all_products[query.offset:query.offset + query.limit]
        
        return [{
            'id': p.id,
            'seller_id': p.seller_id,
            'name': p.name,
            'price': p.price.amount,
            'quantity': p.quantity,
            'is_active': p.is_active,
        } for p in products]
