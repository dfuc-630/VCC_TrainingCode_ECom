from ddd.shared.infrastructure.repository import Repository, QueryRepository
from typing import Optional, List


class ProductRepository(Repository):
    """Repository interface for Product persistence"""
    
    def find_by_seller_id(self, seller_id: str) -> List:
        """Find all products for a seller"""
        raise NotImplementedError
    
    def find_active(self, skip: int = 0, limit: int = 100) -> List:
        """Find all active products"""
        raise NotImplementedError
    
    def find_by_name(self, name: str) -> Optional:
        """Find product by name"""
        raise NotImplementedError
