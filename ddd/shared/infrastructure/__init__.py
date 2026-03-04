"""
Shared infrastructure - init file
"""
from ddd.shared.infrastructure.repository import Repository, QueryRepository
from ddd.shared.infrastructure.unit_of_work import UnitOfWork, TransactionManager
from ddd.shared.infrastructure.event_dispatcher import (
    EventDispatcher,
    EventHandler,
    InMemoryEventDispatcher,
    KafkaEventDispatcher,
)

__all__ = [
    'Repository',
    'QueryRepository',
    'UnitOfWork',
    'TransactionManager',
    'EventDispatcher',
    'EventHandler',
    'InMemoryEventDispatcher',
    'KafkaEventDispatcher',
]
