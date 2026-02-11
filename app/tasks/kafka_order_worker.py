from kafka import KafkaConsumer
import json
import logging
import os
import signal
from datetime import datetime, timedelta
from typing import Dict, Set
from collections import defaultdict
from sqlalchemy import func
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.wallet import Wallet
from app.enums import OrderStatus, OrderItemStatus, PaymentStatus
from app.extensions import db
from app.services.wallet_service import WalletService

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


KAFKA_BOOTSTRAP_SERVERS = "10.5.68.163:9092"
CONSUMER_GROUP = "order-workers"
MAX_RETRY = 5


class OrderResultAggregator:
    def __init__(self):
        # Map: order_id -> set of completed order_item_ids
        self.completed_items: Dict[str, Set[str]] = defaultdict(set)
        # Map: order_id -> set of failed order_item_ids
        self.failed_items: Dict[str, Set[str]] = defaultdict(set)
        # Map: order_id -> total expected items count
        self.expected_counts: Dict[str, int] = {}
    
    def add_result(self, order_id: str, order_item_id: str, status: str):
        if status == "RESERVED":
            self.completed_items[order_id].add(order_item_id)
        elif status == "FAILED":
            self.failed_items[order_id].add(order_item_id)
    
    def set_expected_count(self, order_id: str, count: int):
        self.expected_counts[order_id] = count
    
    def is_order_complete(self, order_id: str) -> tuple[bool, str]:
        expected = self.expected_counts.get(order_id)
        if expected is None:
            return False, "INCOMPLETE"
        
        completed = len(self.completed_items[order_id])
        failed = len(self.failed_items[order_id])
        total_processed = completed + failed
        
        if total_processed < expected:
            return False, "INCOMPLETE"
        
        if failed > 0:
            return True, "FAILED"
        else:
            return True, "SUCCESS"
    
    def clear_order(self, order_id: str):
        self.completed_items.pop(order_id, None)
        self.failed_items.pop(order_id, None)
        self.expected_counts.pop(order_id, None)


class OrderKafkaWorker:
    """Kafka consumer worker for order finalization"""
    
    def __init__(self, worker_id: int = 1):
        self.worker_id = worker_id
        self.running = True
        self.aggregator = OrderResultAggregator()
        
        self.consumer = KafkaConsumer(
            'order-item-result',
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=CONSUMER_GROUP,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            auto_offset_reset='earliest',
            enable_auto_commit=False,
            max_poll_records=50,  # Process more results in batch
            session_timeout_ms=30000,
            heartbeat_interval_ms=10000,
        )
        
        logger.info(f"OrderWorker-{worker_id} initialized")
    
    def lock_wallets(self, order: Order) -> Dict[str, Wallet]:
        wallet_ids = sorted([
            order.customer.wallet.id,
            order.seller.wallet.id
        ])
        
        wallets = (
            db.session.query(Wallet)
            .filter(Wallet.id.in_(wallet_ids))
            .with_for_update()
            .all()
        )
        
        return {w.id: w for w in wallets}
    
    def rollback_stock(self, order_id: str):
        items = db.session.query(OrderItem).filter(
            OrderItem.order_id == order_id,
            OrderItem.status == OrderItemStatus.RESERVED
        ).all()
        
        product_ids = sorted({i.product_id for i in items})
        products = (
            db.session.query(Product)
            .filter(Product.id.in_(product_ids))
            .with_for_update()
            .all()
        )
        
        product_map = {p.id: p for p in products}
        
        for item in items:
            product_map[item.product_id].stock_quantity += item.quantity
        
        logger.info(f"Rolled back stock for order {order_id}, {len(items)} items")
    
    def process_success(self, order: Order):
        if order.status in [OrderStatus.COMPLETED, OrderStatus.FAILED, OrderStatus.CANCELLED]:
            logger.warning(f"Order {order.id} already in final status {order.status.value}")
            return
        
        try:
            wallets = self.lock_wallets(order)
            
            WalletService.deduct_atomic(
                wallet=wallets[order.customer.wallet.id],
                amount=order.total_amount,
                order_id=order.id,
                description=f"Payment for order {order.order_number}"
            )
            
            WalletService.deposit_atomic(
                wallet=wallets[order.seller.wallet.id],
                amount=order.total_amount,
                order_id=order.id,
                description=f"Income from order {order.order_number}"
            )
            
            updated_count = db.session.query(OrderItem).filter(
                OrderItem.order_id == order.id,
                OrderItem.status == OrderItemStatus.RESERVED
            ).update(
                {OrderItem.status: OrderItemStatus.COMPLETED},
                synchronize_session=False
            )
            
            order.status = OrderStatus.COMPLETED
            order.payment_status = PaymentStatus.PAID
            
            db.session.commit()
            logger.info(
                f"Order {order.id} COMPLETED successfully "
                f"({updated_count} items, amount={order.total_amount})"
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to process successful order {order.id}: {e}")
            raise
    
    def process_failed(self, order: Order):
        if order.status in [OrderStatus.COMPLETED, OrderStatus.FAILED, OrderStatus.CANCELLED]:
            logger.warning(f"Order {order.id} already in final status {order.status.value}")
            return
        
        try:
            self.rollback_stock(order.id)
            
            updated_count = db.session.query(OrderItem).filter(
                OrderItem.order_id == order.id,
                ~OrderItem.status.in_([
                    OrderItemStatus.CANCELLED, 
                    OrderItemStatus.COMPLETED
                ])
            ).update(
                {OrderItem.status: OrderItemStatus.CANCELLED},
                synchronize_session=False
            )
            
            order.status = OrderStatus.CANCELLED
            order.payment_status = PaymentStatus.UNPAID
            
            db.session.commit()
            logger.info(
                f"Order {order.id} CANCELLED/FAILED "
                f"({updated_count} items cancelled)"
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to process failed order {order.id}: {e}")
            raise
    
    def finalize_order(self, order_id: str):
        is_complete, result = self.aggregator.is_order_complete(order_id)
        
        if not is_complete:
            return  # Wait for more results
        
        try:
            order = (
                db.session.query(Order)
                .filter(Order.id == order_id)
                .with_for_update()
                .first()
            )
            
            if not order:
                logger.error(f"Order {order_id} not found in database")
                return
            
            if order.status in [OrderStatus.COMPLETED, OrderStatus.FAILED, OrderStatus.CANCELLED]:
                logger.info(f"Order {order_id} already finalized: {order.status.value}")
                self.aggregator.clear_order(order_id)
                return
            
            if result == "SUCCESS":
                self.process_success(order)
            elif result == "FAILED":
                self.process_failed(order)
            
            # Clear aggregator state
            self.aggregator.clear_order(order_id)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error finalizing order {order_id}: {e}", exc_info=True)
    
    
    """
        Load expected item counts for in-flight orders on startup
        This ensures aggregator knows how many items to expect
        """
    def load_expected_counts(self):
        try:
            results = (
                db.session.query(
                    Order.id,
                    func.count(OrderItem.id).label('item_count')
                )
                .join(OrderItem, OrderItem.order_id == Order.id)
                .filter(
                    ~Order.status.in_([
                        OrderStatus.COMPLETED, 
                        OrderStatus.FAILED, 
                        OrderStatus.CANCELLED
                    ])
                )
                .group_by(Order.id)
                .all()
            )
            
            for order_id, item_count in results:
                self.aggregator.set_expected_count(order_id, item_count)
            
            logger.info(f"Loaded expected counts for {len(results)} in-flight orders")
            
        except Exception as e:
            logger.error(f"Failed to load expected counts: {e}")
    
    def process_message(self, message):
        try:
            data = message.value
            order_item_id = data['order_item_id']
            order_id = data['order_id']
            status = data['status']  # RESERVED or FAILED
            
            logger.info(
                f"[Worker-{self.worker_id}] Received result: "
                f"order={order_id}, item={order_item_id}, status={status}"
            )
            
            # First time seeing this order? Load expected count
            if order_id not in self.aggregator.expected_counts:
                order = db.session.query(Order).filter(Order.id == order_id).first()
                if order:
                    item_count = db.session.query(OrderItem).filter(
                        OrderItem.order_id == order_id
                    ).count()
                    self.aggregator.set_expected_count(order_id, item_count)
            
            # Add result to aggregator
            self.aggregator.add_result(order_id, order_item_id, status)
            
            # Try to finalize order
            self.finalize_order(order_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing result message: {e}", exc_info=True)
            db.session.rollback()
            return False
    
    def run(self):
        logger.info(f"OrderWorker-{self.worker_id} started (PID={os.getpid()})")
        
        # Load expected counts on startup
        self.load_expected_counts()
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)
        
        try:
            while self.running:
                messages = self.consumer.poll(timeout_ms=1000)
                
                if not messages:
                    continue
                
                for topic_partition, records in messages.items():
                    for message in records:
                        success = self.process_message(message)
                        
                        if success:
                            self.consumer.commit()
                        else:
                            logger.warning(
                                f"Skipping commit for failed message at offset {message.offset}"
                            )
                
        except Exception as e:
            logger.error(f"Consumer loop error: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def _shutdown(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down worker-{self.worker_id}...")
        self.running = False
    
    def cleanup(self):
        logger.info(f"Cleaning up OrderWorker-{self.worker_id}")
        self.consumer.close()
        logger.info(f"OrderWorker-{self.worker_id} stopped")


def run_order_kafka_worker(worker_id: int = 1):
    worker = OrderKafkaWorker(worker_id)
    worker.run()


if __name__ == "__main__":
    run_order_kafka_worker(worker_id=1)