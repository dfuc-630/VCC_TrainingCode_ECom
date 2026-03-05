"""
Command handler for creating orders
Orchestrates the domain logic via CreateOrderUseCase
"""
from ddd.order_management.application.dto.order_dto import OrderDTO


class CreateOrderCommandHandler:    
    def __init__(self, create_order_use_case):
        """
            create_order_use_case: CreateOrderUseCase 
        """
        self._use_case = create_order_use_case
    
    def execute(self, command) -> OrderDTO:
        """
            command: CreateOrderCommand
            Returns: OrderDTO with created order details
        """
        # Execute use case (complex orchestration)
        order = self._use_case.execute(command)
        
        # Convert to DTO for API response
        return OrderDTO.from_entity(order)
