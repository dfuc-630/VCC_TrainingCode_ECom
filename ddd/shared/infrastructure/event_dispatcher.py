"""
Event dispatcher for domain events
"""
from abc import ABC, abstractmethod
from typing import Callable, Dict, List, Type, Optional
import logging

from ddd.shared.domain.base_entity import DomainEvent


logger = logging.getLogger(__name__)


class EventHandler(ABC):
    """Base class for event handlers"""
    
    @abstractmethod
    def handle(self, event: DomainEvent) -> None:
        """Handle a domain event"""
        pass


class EventDispatcher(ABC):
    """
    Abstract event dispatcher for publishing domain events.
    
    This allows decoupling between domains through event-driven architecture.
    """
    
    @abstractmethod
    def subscribe(self, event_type: Type[DomainEvent], handler: Callable) -> None:
        """
        Subscribe to an event type.
        
        Args:
            event_type: The domain event class to subscribe to
            handler: A callable that will handle the event
        """
        pass
    
    @abstractmethod
    def dispatch(self, event: DomainEvent) -> None:
        """
        Dispatch a domain event to all subscribed handlers.

        Args:
            event: The domain event to dispatch
        """
        pass
    
    @abstractmethod
    def send_message(self, topic: str, message: Dict, key: Optional[str] = None) -> bool:
        """
        Send a generic message to a Kafka topic.
        
        Used for internal worker communication (order-item-events, order-events, etc).
        Not for domain events.
        
        Args:
            topic: Kafka topic name
            message: Message dict to publish
            key: Optional partition key (for determining which partition messages go to)
            
        Returns:
            True if successful, False otherwise
        """
        pass


class InMemoryEventDispatcher(EventDispatcher):
    """
    In-memory event dispatcher implementation.
    
    Useful for testing and simple applications. For production,
    consider using a message queue like RabbitMQ or Kafka.
    """
    
    def __init__(self):
        self._subscribers: Dict[Type[DomainEvent], List[Callable]] = {}
    
    def subscribe(self, event_type: Type[DomainEvent], handler: Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Handler {handler.__class__.__name__} subscribed to {event_type.__name__}")
    
    def dispatch(self, event: DomainEvent) -> None:
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])
        
        for handler in handlers:
            try:
                logger.info(f"Dispatching {event_type.__name__} to {handler.__class__.__name__}")
                handler(event)
            except Exception as e:
                logger.error(f"Error handling event {event_type.__name__}: {e}", exc_info=True)
    
    def send_message(self, topic: str, message: Dict, key: Optional[str] = None) -> bool:
        """Log message (no-op for in-memory)"""
        logger.info(f"[InMemory] Would send message to topic '{topic}' (key={key}): {message}")
        return True


class KafkaEventDispatcher(EventDispatcher):
    """
    Kafka-based event dispatcher for distributed event publishing.
    
    This is suitable for production environments where events need to be
    published to other services asynchronously.
    """
    
    def __init__(self, kafka_producer=None):
        self._kafka_producer = kafka_producer
        self._subscribers: Dict[Type[DomainEvent], List[Callable]] = {}
    
    def subscribe(self, event_type: Type[DomainEvent], handler: Callable) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Handler {handler.__class__.__name__} subscribed to {event_type.__name__}")
    
    def dispatch(self, event: DomainEvent) -> None:
        """Dispatch event via Kafka"""
        if self._kafka_producer:
            try:
                event_type = type(event).__name__
                topic = f"{self._get_topic_from_event(event_type)}"
                
                # Publish to Kafka
                message = {
                    'event_type': event_type,
                    'event_id': event.event_id,
                    'occurred_at': event.occurred_at.isoformat(),
                    'data': event.__dict__,
                }
                self._kafka_producer.send(topic, value=message)
                logger.info(f"Event {event_type} published to Kafka topic {topic}")
            except Exception as e:
                logger.error(f"Error publishing event to Kafka: {e}", exc_info=True)

        # Also call local handlers (sync)
        event_type = type(event)
        handlers = self._subscribers.get(event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}", exc_info=True)
    
    def send_message(self, topic: str, message: Dict, key: Optional[str] = None) -> bool:
        """Send a generic message to Kafka"""
        if not self._kafka_producer:
            logger.warning(f"Kafka producer not available to send message to topic: {topic}")
            return False
        
        try:
            future = self._kafka_producer.send(topic, value=message, key=key)
            future.get(timeout=10)
            logger.info(f"Message sent to Kafka topic: {topic} (key={key})")
            return True
        except Exception as e:
            logger.error(f"Error sending message to topic {topic}: {e}", exc_info=True)
            return False
    
    @staticmethod
    def _get_topic_from_event(event_type_name: str) -> str:
        """Convert event type name to Kafka topic name"""
        # Example: OrderCreatedEvent -> order-created-events
        import re
        name = re.sub(r'(?<!^)(?=[A-Z])', '-', event_type_name).lower()
        return f"{name}s" if not name.endswith('s') else name
