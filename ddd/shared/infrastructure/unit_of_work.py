"""
Unit of Work pattern implementation
"""
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Optional


class UnitOfWork(ABC):
    """
    Unit of Work pattern for transaction management.
    
    Manages database transactions and ensures consistency across multiple repository operations.
    """
    
    @abstractmethod
    def begin(self) -> None:
        """Begin a transaction"""
        pass
    
    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction"""
        pass
    
    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction"""
        pass
    
    @contextmanager
    def transaction(self):
        """
        Context manager for transaction handling.
        
        Usage:
            with unit_of_work.transaction():
                # Perform operations
                pass
        """
        try:
            self.begin()
            yield self
            self.commit()
        except Exception as e:
            self.rollback()
            raise


class TransactionManager:
    """Manages database transactions"""
    
    def __init__(self, unit_of_work: UnitOfWork):
        self._unit_of_work = unit_of_work
    
    @contextmanager
    def transaction(self):
        yield self._unit_of_work.transaction()
