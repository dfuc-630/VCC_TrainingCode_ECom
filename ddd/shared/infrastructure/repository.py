"""
Repository pattern interface
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar('T')


class Repository(ABC, Generic[T]):
    """
    Abstract repository interface.
    
    The repository pattern abstracts data access and provides a collection-like interface
    to work with aggregates.
    """
    
    @abstractmethod
    def save(self, entity: T) -> None:
        """
        Save an entity (insert or update).
        
        Args:
            entity: The entity to save
            
        Raises:
            RepositoryError: If the save operation fails
        """
        pass
    
    @abstractmethod
    def find_by_id(self, entity_id: str) -> Optional[T]:
        """
        Find an entity by its ID.
        
        Args:
            entity_id: The entity ID
            
        Returns:
            The entity if found, None otherwise
            
        Raises:
            RepositoryError: If the find operation fails
        """
        pass
    
    @abstractmethod
    def delete(self, entity_id: str) -> None:
        """
        Delete an entity by its ID.
        
        Args:
            entity_id: The entity ID to delete
            
        Raises:
            RepositoryError: If the delete operation fails
        """
        pass


class QueryRepository(ABC, Generic[T]):
    """
    Query repository interface for read operations.
    
    This is separated from the write repository to follow CQRS pattern.
    """
    
    @abstractmethod
    def find_all(self) -> List[T]:
        """
        Find all entities.
        
        Returns:
            List of all entities
        """
        pass
    
    @abstractmethod
    def find_by_filter(self, **filters) -> List[T]:
        """
        Find entities by filter.
        
        Args:
            **filters: Filter conditions
            
        Returns:
            List of entities matching the filters
        """
        pass
