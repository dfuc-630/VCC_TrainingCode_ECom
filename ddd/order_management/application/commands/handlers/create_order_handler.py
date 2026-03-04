"""
Command handler for creating orders
Orchestrates the domain logic via CreateOrderUseCase
"""
from ddd.order_management.application.dto.order_dto import OrderDTO


class CreateOrderCommandHandler:
    """Handler for creating orders"""
    
    def __init__(self, create_order_use_case):
        """
        Args:
            create_order_use_case: CreateOrderUseCase instance
        """
        self._use_case = create_order_use_case
    
    def execute(self, command) -> OrderDTO:
        """
        Execute order creation
        
        Args:
            command: CreateOrderCommand
            
        Returns:
            OrderDTO with created order details
        """
        # Execute use case (complex orchestration)
        order = self._use_case.execute(command)
        
        # Convert to DTO for API response
        return OrderDTO.from_entity(order)
