"""
Create order use case
"""
from typing import List, Tuple
from ddd.shared.domain.value_objects import Money
from ddd.order_management.domain.entities import Order
from ddd.order_management.domain.repositories import OrderRepository
from ddd.order_management.domain.exceptions import (
    InsufficientStockError,
    InsufficientBalanceError,
)
from ddd.shared.infrastructure import EventDispatcher


class CreateOrderUseCase:
    """
    Create order use case.
    
    Orchestrates:
    1. Load product information
    2. Reserve inventory (Redis)
    3. Create order aggregate
    4. Validate customer balance
    5. Persist order
    6. Dispatch events
    """
    
    def __init__(
        self,
        order_repository: OrderRepository,
        product_repository,  # From product domain
        wallet_repository,   # From payment domain
        inventory_service,   # Inventory service
        event_dispatcher: EventDispatcher,
    ):
        self._order_repository = order_repository
        self._product_repository = product_repository
        self._wallet_repository = wallet_repository
        self._inventory_service = inventory_service
        self._event_dispatcher = event_dispatcher
    
    def execute(self, command) -> Order:
        """
        Execute create order command.
        
        Process:
        1. Validate inputs
        2. Load products and check prices
        3. Reserve inventory (Redis Lua script for atomicity)
        4. Create order aggregate
        5. Save to repository
        6. Dispatch events to Kafka
        
        On failure:
        - Rollback Redis inventory reservation
        - Raise domain exception
        """
        # Extract and prepare data
        customer_id = command.customer_id
        seller_id = command.seller_id
        
        # 1. Load products
        products_map = self._load_products(command.items)
        
        # 2. Prepare order items with prices
        order_items_data = self._prepare_order_items(command.items, products_map)
        
        # 3. Try to reserve inventory (all-or-nothing)
        reserved, message = self._inventory_service.reserve_items(order_items_data)
        if not reserved:
            raise InsufficientStockError(f"Cannot reserve stock: {message}")
        
        try:
            # 4. Validate customer has enough balance
            customer_wallet = self._wallet_repository.find_by_user_id(customer_id)
            if not customer_wallet:
                raise ValueError("Customer wallet not found")
            
            total_amount = sum(
                Money(item['price']) * item['quantity']
                for item in order_items_data
            )
            
            if customer_wallet.balance < total_amount:
                # Rollback inventory
                self._inventory_service.rollback_items(order_items_data)
                raise InsufficientBalanceError("Customer has insufficient balance")
            
            # 5. Create order aggregate
            order = Order.create(
                customer_id=customer_id,
                seller_id=seller_id,
                shipping_address=command.shipping_address,
                shipping_phone=command.shipping_phone,
            )
            
            # Add items to order
            for item_data in order_items_data:
                order.add_item(
                    product_id=item_data['product_id'],
                    product_name=item_data['product_name'],
                    price=Money(item_data['price']),
                    quantity=item_data['quantity'],
                )
            
            # 6. Persist order
            self._order_repository.save(order)
            
            # 7. Dispatch events (async Kafka publishing)
            for event in order.get_uncommitted_events():
                self._event_dispatcher.dispatch(event)
            
            # 8. Publish order item events for worker processing
            self._publish_order_item_events(order)
            
            order.clear_uncommitted_events()
            
            return order
        
        except Exception as e:
            # Rollback inventory on any error
            self._inventory_service.rollback_items(order_items_data)
            raise
    
    def _load_products(self, items: List) -> dict:
        """Load products from catalog domain"""
        product_ids = [item.product_id for item in items]
        return self._product_repository.find_by_ids(product_ids)
    
    def _prepare_order_items(self, items: List, products_map: dict) -> List[dict]:
        """Prepare order items with price information"""
        order_items = []
        for item in items:
            product = products_map.get(item.product_id)
            if not product:
                raise ValueError(f"Product {item.product_id} not found")
            
            order_items.append({
                'product_id': product.id,
                'product_name': product.name,
                'price': product.current_price,
                'quantity': item.quantity,
            })
        
        return order_items
    
    def _publish_order_item_events(self, order: Order) -> None:
        """Publish events for each order item to Kafka"""
        for item in order.items:
            event_data = {
                'order_id': order.id,
                'order_item_id': item.id,
                'product_id': item.product_id,
                'quantity': item.quantity,
                'event_type': 'PROCESS_ITEM',
            }
            # Send to Kafka for worker processing
            self._event_dispatcher.dispatch(event_data)
