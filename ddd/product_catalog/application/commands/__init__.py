"""
Product catalog commands
"""
from .product_commands import (
    CreateProductCommand,
    UpdateProductCommand,
    ActivateProductCommand,
    DeactivateProductCommand,
)

__all__ = [
    'CreateProductCommand',
    'UpdateProductCommand',
    'ActivateProductCommand',
    'DeactivateProductCommand',
]
