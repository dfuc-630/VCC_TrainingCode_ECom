from kafka import KafkaConsumer
import json
import logging
import time
import os
import signal
import sys
from datetime import datetime, timedelta
from typing import Optional
from decimal import Decimal

from app.models.order import OrderItem
from app.models.product import Product
from app.enums import OrderItemStatus
from app.extensions import db
from services.kafka_producer_order_service import get_kafka_producer
from dlq_handler import DLQManager

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


RETRY_LIMIT = 5
RETRY_DELAY = 0.1
PROCESSING_TIMEOUT = timedelta(minutes=2)
KAFKA_BOOTSTRAP_SERVERS = "10.5.68.163:9092"
CONSUMER_GROUP = "order-item-workers"
MAX_MESSAGE_RETRIES = 3  # Max retries before sending to DLQ


class OrderItemKafkaWorker:
    """Kafka consumer worker for order item processing"""
    
    def __init__(self, worker_id: int = 1):
        self.worker_id = worker_id
        self.running = True
        self.kafka_producer = get_kafka_producer()
        self.dlq_manager = DLQManager()
        
        # Track retry counts per message
        self.message_retry_counts = {}  # key: (partition, offset) -> count
        
        # Setup Kafka consumer
        self.consumer = KafkaConsumer(
            'order-item-events',
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=CONSUMER_GROUP,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            auto_offset_reset='earliest',
            enable_auto_commit=False,  # Manual commit for exactly-once semantics
            max_poll_records=10,
            session_timeout_ms=30000,
            heartbeat_interval_ms=10000,
        )
        
        logger.info(f"OrderItemWorker-{worker_id} initialized")
    
    def try_reserve_stock(self, order_item_id: str, product_id: str, quantity: int) -> tuple[bool, Optional[str]]:
        for attempt in range(RETRY_LIMIT):
            try:
                product = (db.session.query(Product).filter(Product.id == product_id).first())
                
                if not product:
                    return False, f"Product {product_id} not found"
                
                if product.stock_quantity < quantity:
                    return False, f"Insufficient stock: {product.stock_quantity} < {quantity}"
                
                # Optimistic lock update
                rows = (
                    db.session.query(Product)
                    .filter(
                        Product.id == product.id,
                        Product.version == product.version,
                        Product.stock_quantity >= quantity
                    )
                    .update(
                        {
                            Product.stock_quantity: Product.stock_quantity - quantity,
                            Product.version: Product.version + 1
                        },
                        synchronize_session=False
                    )
                )
                
                if rows == 1:
                    db.session.commit()
                    logger.info(
                        f"Reserved stock: order_item={order_item_id}, "
                        f"product={product_id}, quantity={quantity}"
                    )
                    return True, None
                
                # Version conflict, retry
                db.session.rollback()
                time.sleep(RETRY_DELAY * (attempt + 1))
                
            except Exception as e:
                db.session.rollback()
                logger.error(f"Stock reservation error (attempt {attempt+1}): {e}")
                if attempt == RETRY_LIMIT - 1:
                    return False, str(e)
                time.sleep(RETRY_DELAY)
        
        return False, f"Failed after {RETRY_LIMIT} retries"
    
    def update_order_item_status(self, order_item_id: str, status: OrderItemStatus):
        try:
            order_item = (
                db.session.query(OrderItem)
                .filter(OrderItem.id == order_item_id)
                .first()
            )
            
            if order_item:
                if order_item.status not in [OrderItemStatus.RESERVED, OrderItemStatus.FAILED, OrderItemStatus.CANCELLED]:
                    order_item.status = status
                    db.session.commit()
                    logger.info(f"Updated OrderItem {order_item_id} status to {status.value}")
                else:
                    logger.warning(f"OrderItem {order_item_id} already in final status: {order_item.status.value}")
            else:
                logger.error(f"OrderItem {order_item_id} not found in database")
                
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to update OrderItem status: {e}")
    
    def process_message(self, message):
        message_id = (message.partition, message.offset)
        retry_count = self.message_retry_counts.get(message_id, 0)
        
        try:
            data = message.value
            order_item_id = data['order_item_id']
            order_id = data['order_id']
            product_id = data['product_id']
            quantity = data['quantity']
            event_type = data.get('event_type', 'PROCESS_ITEM')
            
            logger.info(
                f"[Worker-{self.worker_id}] Processing: "
                f"order_item={order_item_id}, event_type={event_type}, "
                f"retry_count={retry_count}"
            )
            
            # Update status to PROCESSING
            self.update_order_item_status(order_item_id, OrderItemStatus.PROCESSING)
            
            # Try to reserve stock
            success, error_message = self.try_reserve_stock(order_item_id, product_id, quantity)
            
            # Update final status in DB
            final_status = OrderItemStatus.RESERVED if success else OrderItemStatus.FAILED
            self.update_order_item_status(order_item_id, final_status)
            
            # Publish result to Kafka
            result_published = self.kafka_producer.publish_order_item_result(
                order_item_id=order_item_id,
                order_id=order_id,
                status="RESERVED" if success else "FAILED",
                error_message=error_message,
                retry_count=retry_count
            )
            
            if not result_published:
                logger.error(f"Failed to publish result for order_item {order_item_id}")
                raise Exception("Failed to publish result to Kafka")
            
            if message_id in self.message_retry_counts:
                del self.message_retry_counts[message_id]
            
            logger.info(
                f"[Worker-{self.worker_id}] Completed: "
                f"order_item={order_item_id}, status={final_status.value}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            db.session.rollback()
            
            retry_count += 1
            self.message_retry_counts[message_id] = retry_count
            
            self.dlq_manager.handle_processing_failure(
                topic="order-item-events",
                message_key=message.key,
                message_value=message.value,
                error=e,
                retry_count=retry_count,
                partition=message.partition,
                offset=message.offset
            )
            
            if retry_count < MAX_MESSAGE_RETRIES:
                return False
            else:
                logger.error(
                    f"Max retries reached for message at offset {message.offset}. "
                    "Message sent to DLQ. Committing offset."
                )
                return True
    
    def run(self):
        logger.info(f"OrderItemWorker-{self.worker_id} started (PID={os.getpid()})")
        
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
                            # Could implement DLQ here for persistent failures
                
        except Exception as e:
            logger.error(f"Consumer loop error: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def _shutdown(self, signum, frame):
        logger.info(f"Received signal {signum}, shutting down worker-{self.worker_id}...")
        self.running = False
    
    def cleanup(self):
        logger.info(f"Cleaning up OrderItemWorker-{self.worker_id}")
        self.consumer.close()
        self.dlq_manager.close()
        logger.info(f"OrderItemWorker-{self.worker_id} stopped")


def run_order_item_kafka_worker(worker_id: int = 1):
    worker = OrderItemKafkaWorker(worker_id)
    worker.run()


if __name__ == "__main__":
    run_order_item_kafka_worker(worker_id=1)