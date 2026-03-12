"""
DDD Order Item Kafka Worker
Consumes order-item-events from Kafka and processes them using DDD repositories
"""
from kafka import KafkaConsumer
import json
import logging
import time
import os
import signal
import sys
from datetime import datetime, timedelta
from typing import Optional, Tuple

from ddd.order_management.infrastructure.persistence.sqlalchemy_order_repository import SqlAlchemyOrderRepository
from app.enums import OrderItemStatus

    
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


RETRY_LIMIT = 5
RETRY_DELAY = 0.1
PROCESSING_TIMEOUT = timedelta(minutes=2)
KAFKA_BOOTSTRAP_SERVERS = "10.5.68.163:9092"
CONSUMER_GROUP = "ddd-order-item-workers"
MAX_MESSAGE_RETRIES = 3  # Max retries before sending to DLQ


class DDDOrderItemKafkaWorker:
    """DDD-based Kafka consumer worker for order item processing"""
    
    def __init__(self, worker_id: int = 1):
        self.worker_id = worker_id
        self.running = True
        self.db = None  # Will be set in run()
        
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
        
        logger.info(f"DDDOrderItemWorker-{worker_id} initialized")
    
    def validate_business_rules(
        self, 
        order_item_id: str, 
        order_id: str, 
        product_id: str, 
        quantity: int, 
        event_type: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate business rules for order item processing.
        
        Currently defaults to valid since stock has been reserved at the edge.
        Can be extended for fraud detection, policy checks, etc.
        """
        try:
            _ = int(quantity)
        except Exception:
            return False, f"Quantity {quantity} is not a valid integer"

        if quantity <= 0:
            return False, f"Quantity {quantity} must be greater than 0"
        
        return True, None
    
    def update_order_item_status(self, order_item_id: str, status: OrderItemStatus):
        """Update order item status in database"""
        try:
            from app.models.order import OrderItem
            order_item = (
                self.db.session.query(OrderItem)
                .filter(OrderItem.id == order_item_id)
                .first()
            )
            
            if order_item:
                if order_item.status not in [OrderItemStatus.RESERVED, OrderItemStatus.FAILED, OrderItemStatus.CANCELLED]:
                    order_item.status = status
                    self.db.session.commit()
                    logger.info(f"Updated OrderItem {order_item_id} status to {status.value}")
                else:
                    logger.warning(f"OrderItem {order_item_id} already in final status: {order_item.status.value}")
            else:
                logger.error(f"OrderItem {order_item_id} not found in database")
                
        except Exception as e:
            self.db.session.rollback()
            logger.error(f"Failed to update OrderItem status: {e}")
    
    def publish_item_result(self, order_item_id: str, order_id: str, status: str, error_message: Optional[str] = None, retry_count: int = 0) -> bool:
        """Publish order item result to Kafka"""
        try:
            from app.services.kafka_producer_order_service import get_kafka_producer
            producer = get_kafka_producer()
            
            result_message = {
                'order_item_id': order_item_id,
                'order_id': order_id,
                'status': status,  # 'RESERVED' or 'FAILED'
                'error_message': error_message,
                'retry_count': retry_count,
                'timestamp': datetime.utcnow().isoformat(),
            }
            
            return producer.publish_order_item_result(
                order_item_id=order_item_id,
                order_id=order_id,
                status=status,
                error_message=error_message,
                retry_count=retry_count
            )
        except Exception as e:
            logger.error(f"Failed to publish item result: {e}")
            return False
    
    def process_message(self, message):
        """Process a single Kafka message"""
        message_id = (message.partition, message.offset)
        retry_count = self.message_retry_counts.get(message_id, 0)

        try:
            data = message.value
            order_item_id = str(data['order_item_id'])
            order_id = str(data['order_id'])
            product_id = str(data['product_id'])
            quantity = data['quantity']
            event_type = str(data.get('event_type', 'PROCESS_ITEM'))
            
            logger.info(
                f"[Worker-{self.worker_id}] Processing: "
                f"order_item={order_item_id}, event_type={event_type}, "
                f"retry_count={retry_count}"
            )
            
            # Update status to PROCESSING
            self.update_order_item_status(order_item_id, OrderItemStatus.PROCESSING)
            
            # Business validation
            success, error_message = self.validate_business_rules(
                order_item_id=order_item_id,
                order_id=order_id,
                product_id=product_id,
                quantity=int(quantity),
                event_type=event_type,
            )
            
            # Update final status in DB
            final_status = OrderItemStatus.RESERVED if success else OrderItemStatus.FAILED
            self.update_order_item_status(order_item_id, final_status)
            
            # Publish result to Kafka
            result_published = self.publish_item_result(
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
            if self.db:
                self.db.session.rollback()
            
            retry_count += 1
            self.message_retry_counts[message_id] = retry_count
            
            if retry_count < MAX_MESSAGE_RETRIES:
                return False
            else:
                logger.error(
                    f"Max retries reached for message at offset {message.offset}. "
                    "Committing offset (message discarded)."
                )
                return True
    
    def run(self):
        """Main worker loop"""
        from app import create_app
        from app.extensions import db
        
        app = create_app()
        
        with app.app_context():
            # Store db as instance variable for use in other methods
            self.db = db
            
            logger.info(f"DDDOrderItemWorker-{self.worker_id} started (PID={os.getpid()})")
            
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
        logger.info(f"Cleaning up DDDOrderItemWorker-{self.worker_id}")
        self.consumer.close()
        logger.info(f"DDDOrderItemWorker-{self.worker_id} stopped")


def run_ddd_order_item_kafka_worker(worker_id: int = 1):
    """Entry point for running the worker"""
    worker = DDDOrderItemKafkaWorker(worker_id)
    worker.run()
