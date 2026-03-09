"""
Product catalog command handlers
"""
from .product_command_handlers import (
    CreateProductCommandHandler,
    UpdateProductCommandHandler,
    ActivateProductCommandHandler,
    DeactivateProductCommandHandler,
)

__all__ = [
    'CreateProductCommandHandler',
    'UpdateProductCommandHandler',
    'ActivateProductCommandHandler',
    'DeactivateProductCommandHandler',
]
