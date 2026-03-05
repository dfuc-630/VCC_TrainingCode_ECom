from typing import Optional
from ddd.order_management.application.dto.order_dto import OrderDTO
from ddd.order_management.domain.exceptions import OrderNotFoundError


class ConfirmOrderCommandHandler:
    """Handler for confirming orders"""
    
    def __init__(self, order_repository, event_dispatcher):
        self.order_repository = order_repository
        self.event_dispatcher = event_dispatcher
    
    def execute(self, command) -> OrderDTO:
        """Execute order confirmation"""
        order = self.order_repository.find_by_id(command.order_id)
        if not order:
            raise OrderNotFoundError(f"Order {command.order_id} not found")
        
        # Call domain method
        order.confirm()
        
        # Save
        self.order_repository.save(order)
        
        # Dispatch events
        for event in order.get_uncommitted_events():
            self.event_dispatcher.dispatch(event)
        order.clear_uncommitted_events()
        
        return OrderDTO.from_entity(order)


class ShipOrderCommandHandler:
    """Handler for shipping orders"""
    
    def __init__(self, order_repository, event_dispatcher):
        self.order_repository = order_repository
        self.event_dispatcher = event_dispatcher
    
    def execute(self, command) -> OrderDTO:
        """Execute order shipping"""
        order = self.order_repository.find_by_id(command.order_id)
        if not order:
            raise OrderNotFoundError(f"Order {command.order_id} not found")
        
        order.ship()
        self.order_repository.save(order)
        
        for event in order.get_uncommitted_events():
            self.event_dispatcher.dispatch(event)
        order.clear_uncommitted_events()
        
        return OrderDTO.from_entity(order)


class CompleteOrderCommandHandler:
    """Handler for completing orders"""
    
    def __init__(self, order_repository, event_dispatcher):
        self.order_repository = order_repository
        self.event_dispatcher = event_dispatcher
    
    def execute(self, command) -> OrderDTO:
        """Execute order completion"""
        order = self.order_repository.find_by_id(command.order_id)
        if not order:
            raise OrderNotFoundError(f"Order {command.order_id} not found")
        
        order.complete()
        self.order_repository.save(order)
        
        for event in order.get_uncommitted_events():
            self.event_dispatcher.dispatch(event)
        order.clear_uncommitted_events()
        
        return OrderDTO.from_entity(order)


class CancelOrderCommandHandler:
    """Handler for cancelling orders"""
    
    def __init__(self, order_repository, event_dispatcher):
        self.order_repository = order_repository
        self.event_dispatcher = event_dispatcher
    
    def execute(self, command) -> OrderDTO:
        
        order = self.order_repository.find_by_id(command.order_id)
        if not order:
            raise OrderNotFoundError(f"Order {command.order_id} not found")
        
        order.cancel()
        self.order_repository.save(order)
        
        for event in order.get_uncommitted_events():
            self.event_dispatcher.dispatch(event)
        order.clear_uncommitted_events()
        
        return OrderDTO.from_entity(order)
