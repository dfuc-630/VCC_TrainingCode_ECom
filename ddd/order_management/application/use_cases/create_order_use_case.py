"""
Create order use case
Orchestrates async order processing with Kafka workers
"""
from typing import List, Tuple, Optional
from datetime import datetime, timezone
import logging

from ddd.shared.domain.value_objects import Money
from ddd.order_management.domain.entities import Order
from ddd.order_management.domain.repositories import OrderRepository
from ddd.order_management.domain.exceptions import (
    InsufficientStockError,
    InsufficientBalanceError,
    OrderNotFoundError,
)
from ddd.shared.infrastructure import EventDispatcher

logger = logging.getLogger(__name__)


class CreateOrderUseCase:

    def __init__(self, order_repository: OrderRepository, product_repository,  
        wallet_repository, inventory_service, event_dispatcher: EventDispatcher,):
        
        self._order_repository = order_repository
        self._product_repository = product_repository
        self._wallet_repository = wallet_repository
        self._inventory_service = inventory_service
        self._event_dispatcher = event_dispatcher
    
    def execute(self, command) -> Order:

        customer_id = command.customer_id
        seller_id = command.seller_id
        
        logger.info(f"Creating order for customer={customer_id}, items={len(command.items)}")
        
        try:
            products_map = self._load_products(command.items)
            order_items_data = self._prepare_order_items(command.items, products_map)
            total_amount = self._calculate_total(order_items_data)
            
            logger.info(f"Validated {len(order_items_data)} items, total={total_amount}")
            
            success, message, reservation_id = self._inventory_service.reserve_items(order_items_data)
            if not success:
                logger.warning(f"Stock reservation failed: {message}")
                raise InsufficientStockError(f"Stock reservation failed: {message}")
            
            logger.info(f"Stock reserved: reservation_id={reservation_id}")
            
            customer_wallet = self._wallet_repository.find_by_user_id(customer_id)
            if not customer_wallet:
                self._inventory_service.rollback_items(order_items_data)
                logger.error(f"Customer wallet not found: {customer_id}")
                raise ValueError(f"Wallet not found for customer {customer_id}")
            
            if customer_wallet.balance < total_amount:
                self._inventory_service.rollback_items(order_items_data)
                logger.warning(f"Insufficient balance: wallet={customer_wallet.balance}, required={total_amount}")
                raise InsufficientBalanceError(
                    f"Insufficient balance. Required: {total_amount}, Available: {customer_wallet.balance}"
                )
            
            logger.info(f"Wallet validated: {customer_wallet.balance} >= {total_amount}")
            
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
                    price=Money(float(item_data['price'])),
                    quantity=item_data['quantity'],
                )
            
            logger.info(f"Order aggregate created: order_id={order.id}, order_number={order.order_number}")
            
            self._order_repository.save(order)
            logger.info(f"Order persisted: {order.id}")
            
            self._publish_order_item_events(order, order_items_data)
            logger.info(f"Order-item events published: {len(order.items)} items")
            
            # order.clear_uncommitted_events()
            
            logger.info(f" Order created successfully (async processing started): {order.id}")
            return order
        
        except Exception as e:
            # On ANY error: rollback stock reservation
            logger.error(f"Error creating order: {e}")
            try:
                self._inventory_service.rollback_items(order_items_data)
                logger.info(f"Stock rolled back due to error")
            except Exception as rollback_error:
                logger.error(f"Error during rollback: {rollback_error}")
            
            raise
    
    def _calculate_total(self, order_items_data: List[dict]) -> Money:
        total = 0
        for item in order_items_data:
            total += float(item['price']) * item['quantity']
        return Money(total)
    
    def _load_products(self, items: List) -> dict:
        product_ids = [item.product_id for item in items]
        if not product_ids:
            raise ValueError("No items provided")
        
        # Try batch load if available
        if hasattr(self._product_repository, 'find_by_ids'):
            return self._product_repository.find_by_ids(product_ids)
        
        # Fallback: load individually
        products = {}
        for product_id in product_ids:
            product = self._product_repository.find_by_id(product_id)
            if not product:
                raise ValueError(f"Product not found: {product_id}")
            products[product_id] = product
        
        return products
    
    def _prepare_order_items(self, items: List, products_map: dict) -> List[dict]:
        order_items = []
        
        for item in items:
            # Validate quantity
            if item.quantity <= 0:
                raise ValueError(f"Invalid quantity: {item.quantity}")
            
            # Load product details
            product = products_map.get(item.product_id)
            if not product:
                raise ValueError(f"Product not found: {item.product_id}")
            
            # Get product price (prefer current_price if available)
            price = getattr(product, 'current_price', getattr(product, 'price', 0))
            
            if isinstance(price, Money):
                price = price.amount
            
            order_items.append({
                'product_id': str(product.id),
                'product_name': product.name,
                'price': float(price),
                'quantity': item.quantity,
            })
        
        if not order_items:
            raise ValueError("No valid items to order")
        
        return order_items
    
    def _publish_order_item_events(self, order: Order, order_items_data: List[dict]) -> None:
        try:
            # Publish each order item for worker processing
            for item in order.items:
                event = {
                    'order_id': order.id,
                    'order_item_id': item.id,
                    'product_id': item.product_id,
                    'quantity': item.quantity,
                    'event_type': 'PROCESS_ITEM',
                    'created_at': datetime.now(timezone.utc).isoformat(),
                }
                
                # Send to topic: order-item-events
                # Kafka order item worker listens and processes
                self._event_dispatcher.send_message(
                    topic='order-item-events',
                    message=event,
                    key=str(item.product_id),
                )
                
                logger.info(f"Order-item event published: order_item_id={item.id}, product_id={item.product_id}")
            
            # Also publish order-level event for order worker
            order_event = {
                'order_id': order.id,
                'customer_id': order.customer_id,
                'seller_id': order.seller_id,
                'total_items': len(order.items),
                'total_amount': float(order.total_amount) if order.total_amount else 0,
                'event_type': 'ORDER_CREATED',
                'created_at': datetime.now(timezone.utc).isoformat(),
            }
            
            # Send to topic: order-events
            # Kafka order worker listens and aggregates item results
            self._event_dispatcher.send_message(
                topic='order-events',
                message=order_event,
                key=str(order.id),
            )
            
            logger.info(f"Order event published: order_id={order.id}")
        
        except Exception as e:
            logger.error(f"Error publishing Kafka events: {e}")
            # Don't raise - events are best-effort
            # Order is already saved, async processing is nice-to-have
