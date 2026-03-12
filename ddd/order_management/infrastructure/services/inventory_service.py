"""
Inventory service for managing stock reservations
Uses Redis for atomic operations with Lua script
"""
from typing import List, Tuple, Optional
import redis
import json
import logging

logger = logging.getLogger(__name__)

# Lua script for atomic stock reservation (all-or-nothing)
RESERVE_STOCK_LUA = """
local n = #KEYS
for i = 1, n do
    local current = tonumber(redis.call('GET', KEYS[i]) or "-1")
    local requested = tonumber(ARGV[i])
    if current < 0 then
        return {0, 'MISSING_KEY'}
    end
    if current < requested then
        return {0, 'INSUFFICIENT_STOCK'}
    end
end

for i = 1, n do
    local requested = tonumber(ARGV[i])
    redis.call('DECRBY', KEYS[i], requested)
end

return {1, 'OK'}
"""


class InventoryService:
    """
    Manages inventory reservations with Redis
    Guarantees atomicity using Lua scripts
    Supports all-or-nothing reservation semantics
    """
    
    def __init__(self, product_repository, redis_client=None):
        """
        Args:
            product_repository: Repository for loading products
            redis_client: Redis client (optional, uses default if None)
        """
        self._product_repository = product_repository
        self._redis = redis_client or redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Register Lua script
        try:
            self._reserve_script = self._redis.register_script(RESERVE_STOCK_LUA)
        except Exception as e:
            logger.warning(f"Failed to register Lua script: {e}. Falling back to non-atomic operations.")
            self._reserve_script = None
    
    def _stock_key(self, product_id: str) -> str:
        """Build stock Redis key"""
        return f"stock:{product_id}"
    
    def seed_stock_from_db(self, products: dict) -> None:
        """
        Initialize stock in Redis from database products.
        Uses SET to ensure Redis stock matches DB stock.
        
        Args:
            products: Dict of {product_id: Product entity}
        """
        if not products:
            return
        
        try:
            pipe = self._redis.pipeline()
            for product_id, product in products.items():
                key = self._stock_key(product_id)
                # Get current Redis value
                current_val = int(self._redis.get(key) or 0)
                # Get DB value
                db_val = int(product.quantity) if hasattr(product, 'quantity') else int(product.stock_quantity)
                
                # Only update if DB value is higher (stock was increased) or if no key exists
                if current_val == 0 or db_val > current_val:
                    logger.debug(f"Seeding {key}: DB={db_val}, Redis={current_val}")
                    pipe.set(key, db_val)
            
            result = pipe.execute()
            logger.debug(f"Seeded {len(result)} product stocks")
        except Exception as e:
            logger.error(f"Error seeding stock: {e}", exc_info=True)
    
    def reserve_items(self, items: List[dict]) -> Tuple[bool, str, Optional[str]]:
        """
        Atomically reserve items from inventory (all-or-nothing).
        
        Args:
            items: List of dicts with 'product_id', 'quantity', 'product_name'
            
        Returns:
            Tuple of (success: bool, message: str, reservation_id: str or None)
        """
        try:
            if not items:
                return False, "No items to reserve", None
            
            # Seed stock if needed
            products_map = {}
            for item in items:
                if item['product_id'] not in products_map:
                    product = self._product_repository.find_by_id(item['product_id'])
                    if not product:
                        return False, f"Product {item['product_id']} not found", None
                    products_map[item['product_id']] = product
            
            self.seed_stock_from_db(products_map)
            
            # Build keys and quantities for Lua script
            keys = [self._stock_key(item['product_id']) for item in items]
            quantities = [str(item['quantity']) for item in items]
            print(f"Reserving items: keys={keys}, quantities={quantities}")
            # Execute atomic reservation
            if self._reserve_script:
                result = self._reserve_script(keys=keys, args=quantities)
                if result[0] == 1:
                    # Success - generate reservation ID
                    reservation_id = self._create_reservation_record(items)
                    logger.info(f"Stock reserved: {items}, reservation_id={reservation_id}")
                    return True, "Items reserved successfully", reservation_id
                else:
                    error_reason = result[1]
                    logger.warning(f"Stock reservation failed: {error_reason}")
                    return False, f"Cannot reserve stock: {error_reason}", None
            else:
                # Fallback: non-atomic (for testing)
                for item in items:
                    key = self._stock_key(item['product_id'])
                    current = int(self._redis.get(key) or 0)
                    if current < item['quantity']:
                        logger.warning(f"Insufficient stock for {item['product_id']}")
                        return False, f"Insufficient stock for {item['product_id']}", None
                    self._redis.decrby(key, item['quantity'])
                
                reservation_id = self._create_reservation_record(items)
                logger.info(f"Stock reserved (non-atomic): {items}, reservation_id={reservation_id}")
                return True, "Items reserved successfully", reservation_id
        
        except Exception as e:
            logger.error(f"Exception during stock reservation: {e}")
            return False, f"Error reserving stock: {str(e)}", None
    
    def _create_reservation_record(self, items: List[dict]) -> str:
        """
        Create reservation record in Redis for tracking.
        
        Returns:
            Reservation ID (UUID)
        """
        from uuid import uuid4
        reservation_id = str(uuid4())
        key = f"reservation:{reservation_id}"
        
        # Store items in reservation
        reservation_data = {str(i): json.dumps(item) for i, item in enumerate(items)}
        try:
            self._redis.hset(key, mapping=reservation_data)
            # Set expiration: 1 hour
            self._redis.expire(key, 3600)
        except Exception as e:
            logger.error(f"Error creating reservation record: {e}")
        
        return reservation_id
    
    def rollback_items(self, items: List[dict]) -> bool:
        """
        Rollback inventory reservation (return items to stock).
        
        Args:
            items: List of dicts with 'product_id' and 'quantity'
            
        Returns:
            True if successful
        """
        try:
            pipe = self._redis.pipeline()
            for item in items:
                key = self._stock_key(item['product_id'])
                pipe.incrby(key, item['quantity'])
            pipe.execute()
            logger.info(f"Stock rolled back: {items}")
            return True
        except Exception as e:
            logger.error(f"Error rolling back stock: {e}")
            return False
    
    def release_items(self, items: List[dict]) -> bool:
        """Release reserved items back to inventory (alias for rollback)"""
        return self.rollback_items(items)
    
    def get_stock(self, product_id: str) -> int:
        """
        Get current stock for a product.
        
        Returns:
            Current quantity (0 if key doesn't exist)
        """
        try:
            key = self._stock_key(product_id)
            stock = int(self._redis.get(key) or 0)
            return max(stock, 0)  # Return 0 if negative
        except Exception as e:
            logger.error(f"Error getting stock for {product_id}: {e}")
            return 0
