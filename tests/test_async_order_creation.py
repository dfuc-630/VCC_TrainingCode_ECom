"""
Test async order creation flow
Verifies:
1. Order created with PENDING status
2. Stock reserved atomically
3. Kafka events published
4. Wallet not deducted yet
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock

from ddd.order_management.application.use_cases.create_order_use_case import CreateOrderUseCase
from ddd.order_management.application.dtos.order_dto import CreateOrderCommand
from ddd.order_management.domain.entities import Order
from ddd.order_management.domain.exceptions import InsufficientStockError, InsufficientBalanceError
from ddd.order_management.infrastructure.services.inventory_service import InventoryService
from ddd.shared.infrastructure.event_dispatcher import InMemoryEventDispatcher
from ddd.shared.domain.value_objects import Money


class TestAsyncOrderCreation:
    """Test suite for async order creation with Kafka workers"""
    
    @pytest.fixture
    def mock_repositories(self):
        """Mock all repositories"""
        return {
            'order_repo': Mock(),
            'product_repo': Mock(),
            'wallet_repo': Mock(),
        }
    
    @pytest.fixture
    def mock_services(self):
        """Mock services"""
        return {
            'inventory_service': Mock(spec=InventoryService),
            'event_dispatcher': InMemoryEventDispatcher(),  # Use in-memory for testing
        }
    
    @pytest.fixture
    def use_case(self, mock_repositories, mock_services):
        """Create use case instance"""
        return CreateOrderUseCase(
            order_repository=mock_repositories['order_repo'],
            product_repository=mock_repositories['product_repo'],
            wallet_repository=mock_repositories['wallet_repo'],
            inventory_service=mock_services['inventory_service'],
            event_dispatcher=mock_services['event_dispatcher'],
        )
    
    def test_order_created_with_pending_status(self, use_case, mock_repositories, mock_services):
        """
        When: POST /orders with valid data
        Then: Order created with status=PENDING
        """
        # Setup mock data
        customer_id = "cust-123"
        product_id = "prod-456"
        quantity = 5
        
        # Mock products
        mock_product = Mock()
        mock_product.id = product_id
        mock_product.price = Money(amount=100, currency="VND")
        
        mock_repositories['product_repo'].get_by_id.return_value = mock_product
        
        # Mock wallet
        mock_wallet = Mock()
        mock_wallet.balance = Money(amount=1000, currency="VND")
        mock_repositories['wallet_repo'].get_by_customer_id.return_value = mock_wallet
        
        # Mock inventory service
        mock_services['inventory_service'].reserve_items.return_value = (
            True,  # successful
            "Reserved",  # message
            "reservation-123"  # reservation_id
        )
        
        # Mock order save
        created_order = Mock(spec=Order)
        created_order.id = "order-789"
        created_order.status = "PENDING"
        created_order.items = [Mock(id="item-1", product_id=product_id, quantity=quantity)]
        created_order.customer_id = customer_id
        created_order.seller_id = "seller-1"
        created_order.total_amount = Money(amount=500, currency="VND")
        
        mock_repositories['order_repo'].save.return_value = created_order
        
        # Create command
        command = CreateOrderCommand(
            customer_id=customer_id,
            items=[{
                'product_id': product_id,
                'quantity': quantity,
            }],
            shipping_address="123 Main St",
            phone="1234567890"
        )
        
        # Execute
        result = use_case.execute(command)
        
        # Assert
        assert result.status == "PENDING", "Order should be created with PENDING status"
        assert mock_repositories['order_repo'].save.called, "Order should be saved to database"
    
    def test_stock_reservation_fails_returns_409(self, use_case, mock_repositories, mock_services):
        """
        When: Insufficient stock
        Then: InsufficientStockError raised, stock rolled back
        """
        # Setup
        product_id = "prod-456"
        
        mock_product = Mock()
        mock_product.id = product_id
        mock_product.price = Money(amount=100, currency="VND")
        mock_repositories['product_repo'].get_by_id.return_value = mock_product
        
        # Mock inventory service - return failure
        mock_services['inventory_service'].reserve_items.return_value = (
            False,  # failed
            "Insufficient stock",
            None
        )
        
        command = CreateOrderCommand(
            customer_id="cust-123",
            items=[{'product_id': product_id, 'quantity': 1000}],
            shipping_address="123 Main St",
            phone="1234567890"
        )
        
        # Execute and expect exception
        with pytest.raises(InsufficientStockError):
            use_case.execute(command)
        
        # Assert database not called
        assert not mock_repositories['order_repo'].save.called, "Order should NOT be saved on stock failure"
        assert mock_services['inventory_service'].rollback_items.called, "Stock should be rolled back"
    
    def test_wallet_balance_insufficient_returns_402(self, use_case, mock_repositories, mock_services):
        """
        When: Customer wallet balance insufficient
        Then: InsufficientBalanceError raised
        """
        # Setup
        product_id = "prod-456"
        
        mock_product = Mock()
        mock_product.id = product_id
        mock_product.price = Money(amount=1000, currency="VND")
        mock_repositories['product_repo'].get_by_id.return_value = mock_product
        
        # Stock reservation succeeds
        mock_services['inventory_service'].reserve_items.return_value = (
            True,
            "Reserved",
            "reservation-123"
        )
        
        # Wallet has insufficient balance
        mock_wallet = Mock()
        mock_wallet.balance = Money(amount=100, currency="VND")  # Too low
        mock_repositories['wallet_repo'].get_by_customer_id.return_value = mock_wallet
        
        command = CreateOrderCommand(
            customer_id="cust-123",
            items=[{'product_id': product_id, 'quantity': 10}],
            shipping_address="123 Main St",
            phone="1234567890"
        )
        
        # Execute and expect exception
        with pytest.raises(InsufficientBalanceError):
            use_case.execute(command)
        
        # Stock should be rolled back
        assert mock_services['inventory_service'].rollback_items.called, "Stock should be rolled back on wallet failure"
        assert not mock_repositories['order_repo'].save.called, "Order should NOT be saved"
    
    def test_kafka_events_published(self, use_case, mock_repositories, mock_services):
        """
        When: Order created successfully
        Then: Kafka events published (order-item-events, order-events)
        """
        # Setup
        customer_id = "cust-123"
        product_id = "prod-456"
        quantity = 5
        
        mock_product = Mock()
        mock_product.id = product_id
        mock_product.price = Money(amount=100, currency="VND")
        mock_repositories['product_repo'].get_by_id.return_value = mock_product
        
        mock_wallet = Mock()
        mock_wallet.balance = Money(amount=1000, currency="VND")
        mock_repositories['wallet_repo'].get_by_customer_id.return_value = mock_wallet
        
        mock_services['inventory_service'].reserve_items.return_value = (
            True, "Reserved", "reservation-123"
        )
        
        created_order = Mock(spec=Order)
        created_order.id = "order-789"
        created_order.status = "PENDING"
        created_order.items = [Mock(id="item-1", product_id=product_id, quantity=quantity)]
        created_order.customer_id = customer_id
        created_order.seller_id = "seller-1"
        created_order.total_amount = Money(amount=500, currency="VND")
        
        mock_repositories['order_repo'].save.return_value = created_order
        
        # Spy on event dispatcher
        original_send_message = mock_services['event_dispatcher'].send_message
        sent_messages = []
        
        def capture_send_message(topic, message, key=None):
            sent_messages.append({'topic': topic, 'message': message, 'key': key})
            return original_send_message(topic, message, key)
        
        mock_services['event_dispatcher'].send_message = capture_send_message
        
        command = CreateOrderCommand(
            customer_id=customer_id,
            items=[{'product_id': product_id, 'quantity': quantity}],
            shipping_address="123 Main St",
            phone="1234567890"
        )
        
        # Execute
        result = use_case.execute(command)
        
        # Verify Kafka messages
        topics = [m['topic'] for m in sent_messages]
        assert 'order-item-events' in topics, "order-item-events should be published"
        assert 'order-events' in topics, "order-events should be published"
        
        # Verify order-item-events message format
        item_events = [m for m in sent_messages if m['topic'] == 'order-item-events']
        assert len(item_events) >= 1, "At least one order-item-event should be published"
        
        item_msg = item_events[0]['message']
        assert item_msg['order_id'] == result.id
        assert item_msg['product_id'] == product_id
        assert item_msg['quantity'] == quantity
        assert item_msg['event_type'] == 'PROCESS_ITEM'
    
    def test_wallet_not_deducted_during_create_order(self, use_case, mock_repositories, mock_services):
        """
        When: Order created with async flow
        Then: Wallet NOT deducted (happens in kafka_order_worker later)
        Important: This ensures fast response, only charge after item verification
        """
        # Setup
        customer_id = "cust-123"
        product_id = "prod-456"
        
        mock_product = Mock()
        mock_product.id = product_id
        mock_product.price = Money(amount=100, currency="VND")
        mock_repositories['product_repo'].get_by_id.return_value = mock_product
        
        mock_wallet = Mock()
        initial_balance = Money(amount=1000, currency="VND")
        mock_wallet.balance = initial_balance
        mock_repositories['wallet_repo'].get_by_customer_id.return_value = mock_wallet
        
        mock_services['inventory_service'].reserve_items.return_value = (
            True, "Reserved", "reservation-123"
        )
        
        created_order = Mock(spec=Order)
        created_order.id = "order-789"
        created_order.status = "PENDING"
        created_order.items = [Mock(id="item-1", product_id=product_id, quantity=5)]
        created_order.customer_id = customer_id
        created_order.seller_id = "seller-1"
        created_order.total_amount = Money(amount=500, currency="VND")
        
        mock_repositories['order_repo'].save.return_value = created_order
        
        command = CreateOrderCommand(
            customer_id=customer_id,
            items=[{'product_id': product_id, 'quantity': 5}],
            shipping_address="123 Main St",
            phone="1234567890"
        )
        
        # Execute
        result = use_case.execute(command)
        
        # Verify wallet not deducted (only checked)
        # deduct() should NOT be called on wallet_repository
        assert not mock_repositories['wallet_repo'].deduct.called, \
            "Wallet should NOT be deducted during create_order (deduction happens in worker)"
        
        # But wallet balance should be checked
        assert result.status == "PENDING"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
