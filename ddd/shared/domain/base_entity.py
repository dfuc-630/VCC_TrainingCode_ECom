"""
Base domain entity and aggregate root
"""
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, TypeVar, Generic, Optional
from uuid import uuid4


T = TypeVar('T')


class DomainEvent:
    """Base class for all domain events"""
    
    def __init__(self):
        self.event_id: str = str(uuid4())
        self.occurred_at: datetime = datetime.now(timezone.utc)
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(event_id={self.event_id}, occurred_at={self.occurred_at})"


class Entity(ABC):
    """Base class for domain entities"""
    
    def __init__(self, entity_id: str):
        self._id = entity_id
        self._created_at = datetime.now(timezone.utc)
        self._updated_at = datetime.now(timezone.utc)
    
    @property
    def id(self) -> str:
        return self._id
    
    @property
    def created_at(self) -> datetime:
        return self._created_at
    
    @property
    def updated_at(self) -> datetime:
        return self._updated_at
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, Entity):
            return False
        return self._id == other._id and type(self) == type(other)
    
    def __hash__(self) -> int:
        return hash((self._id, type(self).__name__))
    
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(id={self._id})"


class AggregateRoot(Entity):
    """
    Base class for aggregate roots.
    
    Aggregates are clusters of entities and value objects that are treated as a single unit.
    The aggregate root is the only entry point to the aggregate.
    """
    
    def __init__(self, aggregate_id: str):
        super().__init__(aggregate_id)
        self._uncommitted_events: List[DomainEvent] = []
    
    def raise_domain_event(self, event: DomainEvent) -> None:
        """Raise a domain event that will be dispatched later"""
        self._uncommitted_events.append(event)
    
    def get_uncommitted_events(self) -> List[DomainEvent]:
        """Get all uncommitted domain events"""
        return self._uncommitted_events.copy()
    
    def clear_uncommitted_events(self) -> None:
        """Clear uncommitted events (should be called after dispatch)"""
        self._uncommitted_events.clear()
    
    def has_uncommitted_events(self) -> bool:
        """Check if there are uncommitted events"""
        return len(self._uncommitted_events) > 0
