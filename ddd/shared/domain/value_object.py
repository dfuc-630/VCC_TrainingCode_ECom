"""
Base value object - immutable objects that have no identity
"""
from abc import ABC
from typing import Any


class ValueObject(ABC):
    """
    Base class for value objects.
    
    Value objects are immutable objects that are defined by their attributes,
    not by their identity. Two value objects with the same attributes are considered equal.
    """
    
    def __eq__(self, other) -> bool:
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__
    
    def __hash__(self) -> int:
        # Hash all attributes for use in sets/dicts
        return hash(tuple(sorted(self.__dict__.items())))
    
    def __repr__(self) -> str:
        attrs = ', '.join(f"{k}={v}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"
