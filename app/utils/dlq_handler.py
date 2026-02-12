"""
Dead Letter Queue (DLQ) Handler for failed Kafka messages
"""
from kafka import KafkaConsumer, KafkaProducer
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


KAFKA_BOOTSTRAP_SERVERS = "10.5.68.163:9092"
MAX_RETRY_ATTEMPTS = 3


class DLQProducer:
    """Producer for sending failed messages to DLQ"""
    
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',
            retries=3,
        )
    
    def send_to_dlq(
        self,
        original_topic: str,
        original_message: Dict[str, Any],
        original_key: Optional[str],
        error_message: str,
        retry_count: int,
        original_partition: Optional[int] = None,
        original_offset: Optional[int] = None
    ) -> bool:
        """
        Send failed message to Dead Letter Queue
        
        Args:
            original_topic: Topic where message failed
            original_message: The original message data
            original_key: Original message key
            error_message: Description of the error
            retry_count: Number of retries attempted
            original_partition: Original partition (for tracking)
            original_offset: Original offset (for tracking)
            
        Returns:
            True if sent successfully
        """
        dlq_topic = f"{original_topic}-dlq"
        
        # Enrich message with metadata
        dlq_message = {
            "original_topic": original_topic,
            "original_partition": original_partition,
            "original_offset": original_offset,
            "original_key": original_key,
            "original_message": original_message,
            "error_message": error_message,
            "retry_count": retry_count,
            "failed_at": datetime.utcnow().isoformat(),
        }
        
        try:
            future = self.producer.send(
                dlq_topic,
                key=original_key,
                value=dlq_message
            )
            
            record_metadata = future.get(timeout=10)
            
            logger.warning(
                f"Sent to DLQ: topic={dlq_topic}, "
                f"order_id={original_message.get('order_id')}, "
                f"retry_count={retry_count}, "
                f"error={error_message[:100]}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to send to DLQ: {e}", exc_info=True)
            return False
    
    def close(self):
        """Close producer"""
        self.producer.flush()
        self.producer.close()


class DLQConsumer:
    """
    Consumer for processing DLQ messages
    Attempts to retry or alerts for manual intervention
    """
    
    def __init__(self, dlq_topic: str, group_id: str = "dlq-processor"):
        self.dlq_topic = dlq_topic
        self.consumer = KafkaConsumer(
            dlq_topic,
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            group_id=group_id,
            value_deserializer=lambda m: json.loads(m.decode('utf-8')),
            key_deserializer=lambda k: k.decode('utf-8') if k else None,
            auto_offset_reset='earliest',
            enable_auto_commit=False,
        )
        
        logger.info(f"DLQConsumer initialized for topic: {dlq_topic}")
    
    def process_dlq_message(self, message) -> bool:
        """
        Process a message from DLQ
        
        Strategies:
        1. Log for monitoring/alerting
        2. Attempt to fix and republish
        3. Store in DB for manual review
        
        Returns:
            True if processed successfully
        """
        try:
            data = message.value
            original_message = data['original_message']
            error_message = data['error_message']
            retry_count = data['retry_count']
            
            logger.error(
                f"DLQ Message: "
                f"order_id={original_message.get('order_id')}, "
                f"order_item_id={original_message.get('order_item_id')}, "
                f"retry_count={retry_count}, "
                f"error={error_message}"
            )
            
            # Strategy 1: Alert (send to monitoring system)
            self._send_alert(data)
            
            # Strategy 2: Store in DB for manual review
            self._store_for_review(data)
            
            # Strategy 3: Attempt automatic retry if appropriate
            if retry_count < MAX_RETRY_ATTEMPTS:
                can_retry = self._attempt_retry(data)
                if can_retry:
                    logger.info(f"Scheduled retry for order_item {original_message.get('order_item_id')}")
            else:
                logger.error(
                    f"Max retries exceeded ({retry_count}). Manual intervention required "
                    f"for order_item {original_message.get('order_item_id')}"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing DLQ message: {e}", exc_info=True)
            return False
    
    def _send_alert(self, dlq_data: Dict[str, Any]):
        """
        Send alert to monitoring system
        
        In production, integrate with:
        - PagerDuty
        - Slack
        - Email
        - Custom monitoring
        """
        # TODO: Implement alerting
        logger.critical(
            f"ALERT: DLQ message requires attention: "
            f"order_id={dlq_data['original_message'].get('order_id')}"
        )
    
    def _store_for_review(self, dlq_data: Dict[str, Any]):
        """
        Store DLQ message in database for manual review
        """
        try:
            from app.models.dlq import DLQMessage  # Assuming this model exists
            from app.extensions import db
            
            dlq_record = DLQMessage(
                topic=dlq_data['original_topic'],
                message_key=dlq_data['original_key'],
                message_data=dlq_data['original_message'],
                error_message=dlq_data['error_message'],
                retry_count=dlq_data['retry_count'],
                failed_at=datetime.fromisoformat(dlq_data['failed_at']),
                status='pending_review'
            )
            
            db.session.add(dlq_record)
            db.session.commit()
            
            logger.info(f"Stored DLQ message in DB for review")
            
        except Exception as e:
            logger.error(f"Failed to store DLQ message in DB: {e}")
    
    def _attempt_retry(self, dlq_data: Dict[str, Any]) -> bool:
        """
        Attempt to retry the failed operation
        
        Returns:
            True if retry was attempted
        """
        try:
            # For order item events, we can try to republish
            # or trigger DB polling for that specific order
            
            original_message = dlq_data['original_message']
            order_id = original_message.get('order_id')
            
            if order_id:
                # Option 1: Republish to Kafka
                # from kafka_producer import get_kafka_producer
                # producer = get_kafka_producer()
                # producer.publish_order_item_event(...)
                
                # Option 2: Mark order for DB polling retry
                from app.models.order import Order
                from app.extensions import db
                from app.enums import OrderStatus
                
                order = db.session.query(Order).filter(Order.id == order_id).first()
                if order and order.status not in [OrderStatus.COMPLETED, OrderStatus.CANCELLED]:
                    # Reset to PENDING so DB polling picks it up
                    order.status = OrderStatus.PENDING
                    order.processing_at = None
                    db.session.commit()
                    
                    logger.info(f"Reset order {order_id} to PENDING for DB polling retry")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to retry DLQ message: {e}")
            return False
    
    def run(self):
        """Run DLQ consumer"""
        logger.info(f"Starting DLQ consumer for {self.dlq_topic}...")
        
        try:
            for message in self.consumer:
                success = self.process_dlq_message(message)
                
                if success:
                    self.consumer.commit()
                else:
                    logger.warning(f"Skipping commit for failed DLQ processing")
                    
        except KeyboardInterrupt:
            logger.info("DLQ consumer interrupted")
        finally:
            self.consumer.close()
            logger.info("DLQ consumer stopped")


# DLQ Manager - coordinates DLQ operations
class DLQManager:
    """Manager for DLQ operations"""
    
    def __init__(self):
        self.producer = DLQProducer()
    
    def handle_processing_failure(
        self,
        topic: str,
        message_key: str,
        message_value: Dict,
        error: Exception,
        retry_count: int,
        partition: Optional[int] = None,
        offset: Optional[int] = None
    ):
        """
        Handle a message processing failure
        
        Decides whether to:
        1. Retry immediately
        2. Send to DLQ
        3. Both
        """
        error_message = str(error)
        
        # Send to DLQ if max retries reached
        if retry_count >= MAX_RETRY_ATTEMPTS:
            logger.warning(
                f"Max retries reached for message. Sending to DLQ: "
                f"topic={topic}, key={message_key}"
            )
            
            self.producer.send_to_dlq(
                original_topic=topic,
                original_message=message_value,
                original_key=message_key,
                error_message=error_message,
                retry_count=retry_count,
                original_partition=partition,
                original_offset=offset
            )
        else:
            logger.info(
                f"Retry {retry_count}/{MAX_RETRY_ATTEMPTS} for message: "
                f"topic={topic}, key={message_key}"
            )
    
    def close(self):
        """Clean up resources"""
        self.producer.close()


# Example usage in workers:
"""
from dlq_handler import DLQManager

dlq_manager = DLQManager()

try:
    # Process message
    process_message(message)
except Exception as e:
    dlq_manager.handle_processing_failure(
        topic="order-item-events",
        message_key=message.key,
        message_value=message.value,
        error=e,
        retry_count=current_retry_count,
        partition=message.partition,
        offset=message.offset
    )
"""


# Standalone DLQ consumer script
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python dlq_handler.py <dlq-topic-name>")
        print("Example: python dlq_handler.py order-item-events-dlq")
        sys.exit(1)
    
    dlq_topic = sys.argv[1]
    consumer = DLQConsumer(dlq_topic)
    consumer.run()