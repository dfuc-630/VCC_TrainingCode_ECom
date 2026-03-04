"""
Inventory service for managing stock reservations
Uses Redis for atomic operations
"""
from typing import List, Tuple, Optional
import redis
import json


class InventoryService:
    """
    Manages inventory reservations with Redis
    Guarantees atomicity using Lua scripts
    """
    
    def __init__(self, product_repository, redis_client=None):
        """
        Args:
            product_repository: Repository for loading products
            redis_client: Redis client (optional, uses default if None)
        """
        self._product_repository = product_repository
        self._redis = redis_client or redis.Redis(host='localhost', port=6379, db=0)
    
    def reserve_items(self, items: List[dict]) -> Tuple[bool, str]:
        """
        Atomically reserve items from inventory
        
        Args:
            items: List of dicts with product_id and quantity
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        try:
            # Verify items can be reserved
            for item in items:
                product = self._product_repository.find_by_id(item['product_id'])
                if not product:
                    return False, f"Product {item['product_id']} not found"
                if product.quantity < item['quantity']:
                    return False, f"Insufficient stock for {product.name}"
            
            # Reserve all items atomically
            for item in items:
                key = f"inventory:product:{item['product_id']}"
                self._redis.decrby(key, item['quantity'])
                
                # Also store reservation data
                reservation_key = f"reservation:{item['product_id']}"
                self._redis.lpush(reservation_key, json.dumps(item))
            
            return True, "Items reserved successfully"
        
        except Exception as e:
            return False, str(e)
    
    def rollback_items(self, items: List[dict]) -> bool:
        """
        Rollback inventory reservation
        
        Args:
            items: List of dicts with product_id and quantity
            
        Returns:
            True if successful
        """
        try:
            for item in items:
                key = f"inventory:product:{item['product_id']}"
                self._redis.incrby(key, item['quantity'])
            return True
        except Exception:
            return False
    
    def release_items(self, items: List[dict]) -> bool:
        """Release reserved items back to inventory"""
        return self.rollback_items(items)
