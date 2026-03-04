"""
Shared domain exceptions
"""


class DomainException(Exception):
    """Base exception for all domain exceptions"""
    pass


class InvalidValueObjectError(DomainException):
    """Raised when a value object receives invalid input"""
    pass


class InvalidAggregateError(DomainException):
    """Raised when an aggregate is in an invalid state"""
    pass


class BusinessRuleViolationError(DomainException):
    """Raised when a business rule is violated"""
    pass


class EntityNotFoundError(DomainException):
    """Raised when an entity cannot be found"""
    pass


class RepositoryError(DomainException):
    """Raised when there's a repository operation error"""
    pass


class AggregateNotFoundError(EntityNotFoundError):
    """Raised when an aggregate cannot be found"""
    pass
