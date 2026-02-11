from kafka import KafkaProducer
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class OrderKafkaProducer:
    def __init__(self, bootstrap_servers: str = "10.5.68.163:9092"):
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            key_serializer=lambda k: k.encode('utf-8') if k else None,
            acks='all',  # Wait for all replicas
            retries=3,
            max_in_flight_requests_per_connection=1,  # Ensure ordering
            compression_type='snappy',
            linger_ms=10,  # Batch messages for efficiency
        )
        self.bootstrap_servers = bootstrap_servers
        logger.info(f"Kafka Producer initialized: {bootstrap_servers}")
    


    """
    Publish order item event to order-item-events topic
    
    Args:
        order_item_id: ID of the order item
        order_id: Parent order ID
        product_id: Product ID to reserve
        quantity: Quantity to reserve
        event_type: Type of event (PROCESS_ITEM, RETRY_ITEM, etc.)
    """
    def publish_order_item_event(self, order_item_id: str, order_id: str, product_id: str, 
                                 quantity: int, event_type: str = "PROCESS_ITEM") -> bool:
        topic = "order-item-events"

        message = {
            "order_item_id": order_item_id,
            "order_id": order_id,
            "product_id": product_id,
            "quantity": quantity,
            "event_type": event_type,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            # Use order_id as key for partitioning - items of same order go to same partition
            future = self.producer.send(
                topic,
                key=order_id,
                value=message
            )
            
            # Wait for confirmation (with timeout)
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Published to {topic}: order_item_id={order_item_id}, "
                f"partition={record_metadata.partition}, offset={record_metadata.offset}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish order item event: {e}", exc_info=True)
            return False
    


    """
    Publish order item processing result to order-item-result topic
    
    Args:
        order_item_id: ID of the order item
        order_id: Parent order ID
        status: Processing result (RESERVED/FAILED)
        error_message: Error details if failed
        retry_count: Number of retries attempted
    """
    def publish_order_item_result(self, order_item_id: str, order_id: str, status: str,  
                                  error_message: Optional[str] = None, retry_count: int = 0) -> bool:

        topic = "order-item-result"
        
        message = {
            "order_item_id": order_item_id,
            "order_id": order_id,
            "status": status, # RESERVED or FAILED
            "error_message": error_message,
            "retry_count": retry_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            # Use order_id as key for correct partitioning
            future = self.producer.send(
                topic,
                key=order_id,
                value=message
            )
            
            record_metadata = future.get(timeout=10)
            
            logger.info(
                f"Published to {topic}: order_item_id={order_item_id}, "
                f"status={status}, partition={record_metadata.partition}"
            )
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish order item result: {e}", exc_info=True)
            return False
    


    """
    Publish order-level events (for future use)
    
    Args:
        order_id: Order ID
        event_type: Event type (CREATED, UPDATED, etc.)
        metadata: Additional event data
    """
    def publish_order_event(self, order_id: str, event_type: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        
        topic = "order-events"
        
        message = {
            "order_id": order_id,
            "event_type": event_type,
            "metadata": metadata or {},
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        try:
            future = self.producer.send(
                topic,
                key=order_id,
                value=message
            )
            
            future.get(timeout=10)
            logger.info(f"Published order event: {order_id} - {event_type}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish order event: {e}", exc_info=True)
            return False
    

    def flush(self):
        self.producer.flush()
    
    def close(self):
        self.producer.flush()
        self.producer.close()
        logger.info("Kafka Producer closed")


# Singleton instance
_producer_instance: Optional[OrderKafkaProducer] = None


def get_kafka_producer() -> OrderKafkaProducer:
    """Get or create singleton Kafka producer instance"""
    global _producer_instance
    if _producer_instance is None:
        _producer_instance = OrderKafkaProducer()
    return _producer_instance