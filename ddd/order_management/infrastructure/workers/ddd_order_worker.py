"""
DDD Order Kafka Worker
Consumes order-item-result events from Kafka and finalizes orders
"""
from kafka import KafkaConsumer
import json
import logging
import os
import signal
from datetime import datetime
from typing import Dict, Set
from collections import defaultdict
from decimal import Decimal

from ddd.order_management.infrastructure.persistence.sqlalchemy_order_model import OrderModel, OrderItemModel
from ddd.order_management.domain.value_objects.order import OrderStatus, OrderItemStatus, PaymentStatus
from ddd.payment.domain.entities.wallet import Wallet as DomainWallet
from ddd.payment.infrastructure.persistence.sqlalchemy_wallet_model import WalletModel
from ddd.shared.domain.value_objects import Money
from app.utils.redis_stock import (
    rollback_redis_stock_for_order_items,
    sync_redis_stock_to_db_for_order_items,
)
from uuid import uuid4


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


KAFKA_BOOTSTRAP_SERVERS = "10.5.68.163:9092"
CONSUMER_GROUP = "ddd-order-workers"


class OrderResultAggregator:
    """Aggregates order item results to determine final order status"""
    
    def __init__(self):
        # Map: order_id -> set of completed order_item_ids
        self.completed_items: Dict[str, Set[str]] = defaultdict(set)
        # Map: order_id -> set of failed order_item_ids
        self.failed_items: Dict[str, Set[str]] = defaultdict(set)
        # Map: order_id -> total expected items count
        self.expected_counts: Dict[str, int] = {}
    
    def add_result(self, order_id: str, order_item_id: str, status: str):
        """Add a result for an order item"""
        if status == "RESERVED":
            self.completed_items[order_id].add(order_item_id)
        elif status == "FAILED":
            self.failed_items[order_id].add(order_item_id)
    
    def set_expected_count(self, order_id: str, count: int):
        """Set expected number of items for an order"""
        self.expected_counts[order_id] = count
    
    def is_order_complete(self, order_id: str) -> tuple[bool, str]:
        """Check if all items have been processed and return the result"""
        expected = self.expected_counts.get(order_id)
        if expected is None:
            return False, "INCOMPLETE"
        
        completed = len(self.completed_items[order_id])
        failed = len(self.failed_items[order_id])
        total_processed = completed + failed
        
        logger.debug(f"Order {order_id} status: expected={expected}, completed={completed}, failed={failed}, processed={total_processed}")
        
        if total_processed < expected:
            return False, "INCOMPLETE"
        
        if failed > 0:
            return True, "FAILED"
        else:
            return True, "SUCCESS"
    
    def clear_order(self, order_id: str):
        """Clear aggregated state for an order"""
        self.completed_items.pop(order_id, None)
        self.failed_items.pop(order_id, None)
        self.expected_counts.pop(order_id, None)


class DDDOrderKafkaWorker:
    """DDD-based Kafka consumer worker for order finalization"""
    
    def __init__(self, worker_id: int = 1):
        self.worker_id = worker_id
        self.running = True
        self.aggregator = OrderResultAggregator()
        self.db = None  # Will be set in run()
        
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
        
        logger.info(f"DDDOrderWorker-{worker_id} initialized")
    
    def process_success(self, order_model: OrderModel):
        """Process successful order: sync stock from Redis, transfer funds"""
        if order_model.status in ["completed", "failed", "cancelled"]:
            logger.warning(f"Order {order_model.id} already in final status {order_model.status}")
            return
        
        try:
            # 1. Sync stock from Redis to DB for all items
            items = self.db.session.query(OrderItemModel).filter(
                OrderItemModel.order_id == order_model.id
            ).all()

            sync_redis_stock_to_db_for_order_items(items)
            logger.info(f"Synced Redis stock to DB for {len(items)} items in order {order_model.id}")

            # 2. Lock and transfer wallets using DDD Wallet entity
            # Query wallet ORM models and lock them for atomic update
            wallet_ids = sorted([order_model.customer_id, order_model.seller_id])
            logger.info(f"Looking for wallets for customer_id={order_model.customer_id}, seller_id={order_model.seller_id}")
            
            wallet_models = (
                self.db.session.query(WalletModel)
                .filter(WalletModel.user_id.in_(wallet_ids))
                .with_for_update()
                .all()
            )
            logger.info(f"Found {len(wallet_models)} wallets")
            
            wallet_models_dict = {w.user_id: w for w in wallet_models}
            
            customer_wallet_model = wallet_models_dict.get(order_model.customer_id)
            seller_wallet_model = wallet_models_dict.get(order_model.seller_id)
            
            # Create missing wallets on-demand
            if not customer_wallet_model:
                logger.info(f"Creating missing customer wallet for user_id={order_model.customer_id}")
                customer_wallet_model = WalletModel(
                    id=str(uuid4()),
                    user_id=order_model.customer_id,
                    balance=Decimal('1000000.00'),  # Default initial balance
                    is_active=True
                )
                self.db.session.add(customer_wallet_model)
                self.db.session.flush()
            
            if not seller_wallet_model:
                logger.info(f"Creating missing seller wallet for user_id={order_model.seller_id}")
                seller_wallet_model = WalletModel(
                    id=str(uuid4()),
                    user_id=order_model.seller_id,
                    balance=Decimal('0.00'),  # Sellers start with 0
                    is_active=True
                )
                self.db.session.add(seller_wallet_model)
                self.db.session.flush()
            
            # Convert to DDD Wallet entities
            amount = Money(amount=float(order_model.total_amount))
            
            customer_wallet = DomainWallet(
                wallet_id=customer_wallet_model.id,
                user_id=customer_wallet_model.user_id,
                balance=Money(amount=float(customer_wallet_model.balance))
            )
            seller_wallet = DomainWallet(
                wallet_id=seller_wallet_model.id,
                user_id=seller_wallet_model.user_id,
                balance=Money(amount=float(seller_wallet_model.balance))
            )
            
            # Perform transfers on domain entities
            logger.info(f"Pre-withdrawal: Customer balance={customer_wallet.balance.amount}, Required={amount.amount}")
            
            if not customer_wallet.withdraw(amount):
                logger.error(f"Insufficient balance in customer wallet. Required: {amount.amount}, Available: {customer_wallet.balance.amount}")
                raise ValueError(f"Insufficient balance in customer wallet. Required: {amount.amount}, Available: {customer_wallet.balance.amount}")
            
            logger.info(f"Post-withdrawal: Customer balance={customer_wallet.balance.amount}")
            
            seller_wallet.deposit(amount)
            logger.info(f"Post-deposit: Seller balance={seller_wallet.balance.amount}")
            
            logger.info(f"Wallet transfer: Customer {customer_wallet.user_id} paid {amount.amount} to Seller {seller_wallet.user_id}")
            
            # Update ORM models with new balances
            logger.info(f"Updating wallet models: customer={customer_wallet_model.id} balance={customer_wallet.balance.amount}, seller={seller_wallet_model.id} balance={seller_wallet.balance.amount}")
            customer_wallet_model.balance = Decimal(str(customer_wallet.balance.amount))
            seller_wallet_model.balance = Decimal(str(seller_wallet.balance.amount))
            logger.info(f"Wallet models updated in session. Customer balance: {customer_wallet_model.balance}, Seller balance: {seller_wallet_model.balance}")
            
            # 3. Update all items to COMPLETED
            self.db.session.query(OrderItemModel).filter(
                OrderItemModel.order_id == order_model.id,
                OrderItemModel.status.notin_(["completed"])
            ).update(
                {OrderItemModel.status: "completed"},
                synchronize_session=False
            )
            
            # 4. Update order status
            order_model.status = "completed"
            order_model.payment_status = "paid"
            
            logger.info(f"About to commit: Order {order_model.id}, Customer wallet updated, Seller wallet updated")
            self.db.session.commit()
            logger.info(f"Commit successful! Order {order_model.id} COMPLETED successfully (total_amount={order_model.total_amount})")
            
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Failed to process successful order {order_model.id}: {e}", exc_info=True)
            raise
    
    def process_failed(self, order_model: OrderModel):
        """Process failed order: rollback stock on Redis and cancel items (no wallet operations)"""
        if order_model.status in ["completed", "failed", "cancelled"]:
            logger.warning(f"Order {order_model.id} already in final status {order_model.status}")
            return
        
        try:
            # 1. Rollback stock on Redis for reserved items
            items = self.db.session.query(OrderItemModel).filter(
                OrderItemModel.order_id == order_model.id
            ).all()
            
            rollback_redis_stock_for_order_items(items)
            logger.info(f"Rolled back Redis stock for {len(items)} items in order {order_model.id}")
            
            # 2. Cancel all items (no wallet operations - order was never charged)
            self.db.session.query(OrderItemModel).filter(
                OrderItemModel.order_id == order_model.id,
                OrderItemModel.status.notin_(["cancelled", "completed"])
            ).update(
                {OrderItemModel.status: "cancelled"},
                synchronize_session=False
            )
            
            # 3. Update order status to failed (no wallet refund needed)
            order_model.status = "failed"
            order_model.payment_status = "unpaid"
            
            self.db.session.commit()
            logger.info(f"Order {order_model.id} FAILED - stock rolled back, items cancelled")
            
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Failed to process failed order {order_model.id}: {e}", exc_info=True)
            raise
    
    def finalize_order(self, order_id: str):
        """Finalize order once all items have been processed"""
        is_complete, result = self.aggregator.is_order_complete(order_id)
        
        if not is_complete:
            logger.debug(f"Order {order_id} not yet complete, waiting for more results")
            return  # Wait for more results
        
        try:
            order_model = (
                self.db.session.query(OrderModel)
                .filter(OrderModel.id == order_id)
                .first()
            )
            
            if not order_model:
                logger.error(f"Order {order_id} not found in database")
                return
            
            if order_model.status in ["completed", "failed", "cancelled"]:
                logger.info(f"Order {order_id} already finalized: {order_model.status}")
                self.aggregator.clear_order(order_id)
                return
            
            logger.info(f"Order {order_id} finalization result: {result}")
            
            if result == "SUCCESS":
                self.process_success(order_model)
            elif result == "FAILED":
                self.process_failed(order_model)
            
            # Clear aggregator state
            self.aggregator.clear_order(order_id)
            
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Error finalizing order {order_id}: {e}", exc_info=True)
    
    def load_expected_counts(self):
        """Load expected item counts for in-flight orders on startup"""
        try:
            from sqlalchemy import func
            
            results = (
                self.db.session.query(
                    OrderModel.id,
                    func.count(OrderItemModel.id).label('item_count')
                )
                .join(OrderItemModel, OrderItemModel.order_id == OrderModel.id)
                .filter(
                    ~OrderModel.status.in_([
                        "completed", 
                        "failed", 
                        "cancelled"
                    ])
                )
                .group_by(OrderModel.id)
                .all()
            )
            
            for order_id, item_count in results:
                self.aggregator.set_expected_count(order_id, item_count)
            
            logger.info(f"Loaded expected counts for {len(results)} in-flight orders")
            
        except Exception as e:
            logger.error(f"Failed to load expected counts: {e}")
    
    def process_message(self, message):
        """Process a single Kafka message"""
        try:
            data = message.value
            order_item_id = str(data['order_item_id'])
            order_id = str(data['order_id'])
            status = str(data['status']).upper()  # RESERVED or FAILED
            
            logger.info(
                f"[Worker-{self.worker_id}] Processing result: "
                f"order={order_id}, item={order_item_id}, status={status}"
            )
            
            # First time seeing this order? Load expected count
            if order_id not in self.aggregator.expected_counts:
                order = self.db.session.query(OrderModel).filter(OrderModel.id == order_id).first()
                if order:
                    item_count = self.db.session.query(OrderItemModel).filter(
                        OrderItemModel.order_id == order_id
                    ).count()
                    self.aggregator.set_expected_count(order_id, item_count)
                    logger.info(f"Set expected count for order {order_id}: {item_count} items")
            
            # Add result to aggregator
            self.aggregator.add_result(order_id, order_item_id, status)
            logger.debug(f"Added result to aggregator for order {order_id}")
            
            # Try to finalize order
            self.finalize_order(order_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing result message: {e}", exc_info=True)
            if self.db:
                self.db.session.rollback()
            return False
    
    def run(self):
        """Main worker loop"""
        from app import create_app
        from app.extensions import db
        
        app = create_app()
        
        with app.app_context():
            # Store db as instance variable for use in other methods
            self.db = db
            
            logger.info(f"DDDOrderWorker-{self.worker_id} started (PID={os.getpid()})")
            
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
        logger.info(f"Cleaning up DDDOrderWorker-{self.worker_id}")
        self.consumer.close()
        logger.info(f"DDDOrderWorker-{self.worker_id} stopped")


def run_ddd_order_kafka_worker(worker_id: int = 1):
    """Entry point for running the worker"""
    worker = DDDOrderKafkaWorker(worker_id)
    worker.run()
