"""
Product catalog command handlers
Implements business logic for product operations
"""
import logging
from ddd.product_catalog.domain.entities.product import Product
from ddd.shared.domain.value_objects import Money

logger = logging.getLogger(__name__)


class CreateProductCommandHandler:
    """Handler for creating a new product"""
    
    def __init__(self, product_repository):
        self.product_repository = product_repository
    
    def execute(self, command):
        """
        Execute create product command
        
        Args:
            command: CreateProductCommand
            
        Returns:
            dict with created product info
        """
        logger.info(f"Creating product: {command.name} by seller {command.seller_id}")
        
        # Validate input
        if command.price <= 0:
            raise ValueError("Price must be positive")
        if command.quantity < 0:
            raise ValueError("Quantity must be non-negative")
        
        # Create product aggregate root
        product = Product.create(
            seller_id=command.seller_id,
            name=command.name,
            description=command.description,
            price=Money(amount=command.price, currency='VND'),
            quantity=command.quantity,
        )
        
        # Persist product
        self.product_repository.save(product)
        
        logger.info(f"Product created: {product.id}")
        
        return {
            'id': product.id,
            'name': product.name,
            'price': product.price.amount,
            'quantity': product.quantity,
            'is_active': product.is_active,
        }


class UpdateProductCommandHandler:
    """Handler for updating a product"""
    
    def __init__(self, product_repository):
        self.product_repository = product_repository
    
    def execute(self, command):
        """
        Execute update product command
        
        Args:
            command: UpdateProductCommand
            
        Returns:
            dict with updated product info
            
        Raises:
            Exception: If product not found or unauthorized
        """
        logger.info(f"Updating product: {command.product_id}")
        
        # Find product
        product = self.product_repository.find_by_id(command.product_id)
        if not product:
            raise Exception(f"Product not found: {command.product_id}")
        
        # Check authorization (seller can only update own products)
        if product.seller_id != command.seller_id:
            raise Exception("Unauthorized: You can only update your own products")
        
        # Validate inputs
        if command.price is not None and command.price <= 0:
            raise ValueError("Price must be positive")
        if command.quantity is not None and command.quantity < 0:
            raise ValueError("Quantity must be non-negative")
        
        # Update fields
        if command.name is not None:
            product.name = command.name
        if command.description is not None:
            product.description = command.description
        if command.price is not None:
            product.price = Money(amount=command.price, currency='VND')
        if command.quantity is not None:
            product.quantity = command.quantity
        
        # Persist changes
        self.product_repository.save(product)
        
        logger.info(f"Product updated: {command.product_id}")
        
        return {
            'id': product.id,
            'name': product.name,
            'price': product.price.amount,
            'quantity': product.quantity,
            'is_active': product.is_active,
        }


class ActivateProductCommandHandler:
    """Handler for activating a product"""
    
    def __init__(self, product_repository):
        self.product_repository = product_repository
    
    def execute(self, command):
        """
        Execute activate product command
        
        Args:
            command: ActivateProductCommand
            
        Returns:
            dict with operation result
        """
        logger.info(f"Activating product: {command.product_id}")
        
        # Find product
        product = self.product_repository.find_by_id(command.product_id)
        if not product:
            raise Exception(f"Product not found: {command.product_id}")
        
        # Check authorization
        if product.seller_id != command.seller_id:
            raise Exception("Unauthorized: You can only manage your own products")
        
        # Activate if not already active
        if not product.is_active:
            product.activate()
            self.product_repository.save(product)
            logger.info(f"Product activated: {command.product_id}")
        
        return {
            'id': product.id,
            'is_active': product.is_active,
        }


class DeactivateProductCommandHandler:
    """Handler for deactivating a product"""
    
    def __init__(self, product_repository):
        self.product_repository = product_repository
    
    def execute(self, command):
        """
        Execute deactivate product command
        
        Args:
            command: DeactivateProductCommand
            
        Returns:
            dict with operation result
        """
        logger.info(f"Deactivating product: {command.product_id}")
        
        # Find product
        product = self.product_repository.find_by_id(command.product_id)
        if not product:
            raise Exception(f"Product not found: {command.product_id}")
        
        # Check authorization
        if product.seller_id != command.seller_id:
            raise Exception("Unauthorized: You can only manage your own products")
        
        # Deactivate if not already inactive
        if product.is_active:
            product.deactivate()
            self.product_repository.save(product)
            logger.info(f"Product deactivated: {command.product_id}")
        
        return {
            'id': product.id,
            'is_active': product.is_active,
        }
