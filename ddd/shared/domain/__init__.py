"""
Shared domain - init file
"""
from ddd.shared.domain.base_entity import Entity, AggregateRoot, DomainEvent
from ddd.shared.domain.value_object import ValueObject
from ddd.shared.domain.exceptions import (
    DomainException,
    InvalidValueObjectError,
    InvalidAggregateError,
    BusinessRuleViolationError,
    EntityNotFoundError,
    RepositoryError,
    AggregateNotFoundError,
)

__all__ = [
    'Entity',
    'AggregateRoot',
    'DomainEvent',
    'ValueObject',
    'DomainException',
    'InvalidValueObjectError',
    'InvalidAggregateError',
    'BusinessRuleViolationError',
    'EntityNotFoundError',
    'RepositoryError',
    'AggregateNotFoundError',
]
