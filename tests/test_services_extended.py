import pytest
from decimal import Decimal
from app.services.wallet_service import WalletService
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.extensions import db


class TestWalletServiceExtended:
    """Test wallet service extended functionality"""

    def test_refund_success(self, app, customer_user, product):
        """Test refund to wallet"""
        from app.models.wallet import Wallet
        from app.services.order_service import OrderService

        wallet = Wallet.query.filter_by(user_id=customer_user.id).first()
        initial_balance = wallet.balance

        # Create and cancel order to trigger refund
        order = OrderService.create_order(
            customer_id=customer_user.id,
            items_data=[{"product_id": product.id, "quantity": 1}],
            shipping_address="123 Test St",
            shipping_phone="0901234567",
        )

        # Cancel order (should refund)
        OrderService.cancel_order(order.id, customer_user.id)

        db.session.refresh(wallet)
        assert wallet.balance == initial_balance

    def test_get_transactions_pagination(self, app, customer_user):
        """Test get transactions with pagination"""
        wallet = WalletService.get_wallet_by_user_id(customer_user.id)

        # Create multiple transactions
        for i in range(5):
            WalletService.deposit(
                wallet.id, Decimal("100000.00"), f"Deposit {i}"
            )

        # Get transactions with pagination
        pagination = WalletService.get_transactions(wallet.id, page=1, per_page=2)

        assert pagination.total == 5
        assert len(pagination.items) == 2
        assert pagination.pages == 3


class TestProductServiceExtended:
    """Test product service extended functionality"""

    def test_deduct_stock_success(self, app, product):
        """Test deduct stock"""
        initial_stock = product.stock_quantity

        ProductService.deduct_stock(product.id, 2)

        db.session.refresh(product)
        assert product.stock_quantity == initial_stock - 2

    def test_deduct_stock_insufficient(self, app, product):
        """Test deduct stock with insufficient quantity"""
        product.stock_quantity = 1
        db.session.commit()

        with pytest.raises(ValueError, match="Insufficient stock"):
            ProductService.deduct_stock(product.id, 5)

    def test_deduct_stock_product_not_found(self, app):
        """Test deduct stock for non-existent product"""
        with pytest.raises(ValueError, match="Product not found"):
            ProductService.deduct_stock("invalid-id", 1)


class TestOrderServiceExtended:
    """Test order service extended functionality"""

    def test_get_order_by_id_customer(self, app, customer_user, product):
        """Test get order by id as customer"""
        order = OrderService.create_order(
            customer_id=customer_user.id,
            items_data=[{"product_id": product.id, "quantity": 1}],
            shipping_address="123 Test St",
            shipping_phone="0901234567",
        )

        retrieved = OrderService.get_order_by_id(
            order.id, customer_user.id, "customer"
        )
        assert retrieved.id == order.id

    def test_get_order_by_id_wrong_customer(self, app, customer_user, seller_user, product):
        """Test get order by id as wrong customer"""
        from app.models.user import User
        from app.models.wallet import Wallet

        # Create another customer
        other_customer = User(
            email="other@test.com",
            username="other",
            role="customer",
            is_active=True,
        )
        other_customer.set_password("password123")
        db.session.add(other_customer)
        db.session.flush()

        wallet = Wallet(user_id=other_customer.id)
        db.session.add(wallet)
        db.session.commit()

        order = OrderService.create_order(
            customer_id=customer_user.id,
            items_data=[{"product_id": product.id, "quantity": 1}],
            shipping_address="123 Test St",
            shipping_phone="0901234567",
        )

        with pytest.raises(ValueError, match="Order not found"):
            OrderService.get_order_by_id(order.id, other_customer.id, "customer")

    def test_get_orders_with_filters(self, app, customer_user, product):
        """Test get orders with status filter"""
        # Create orders
        order1 = OrderService.create_order(
            customer_id=customer_user.id,
            items_data=[{"product_id": product.id, "quantity": 1}],
            shipping_address="123 Test St",
            shipping_phone="0901234567",
        )

        # Get pending orders
        pagination = OrderService.get_orders(
            user_id=customer_user.id,
            role="customer",
            status="pending",
        )

        assert pagination.total >= 1
        assert order1.id in [o.id for o in pagination.items]

    def test_cancel_order_already_cancelled(self, app, customer_user, product):
        """Test cancel already cancelled order"""
        order = OrderService.create_order(
            customer_id=customer_user.id,
            items_data=[{"product_id": product.id, "quantity": 1}],
            shipping_address="123 Test St",
            shipping_phone="0901234567",
        )

        # Cancel once
        OrderService.cancel_order(order.id, customer_user.id)

        # Try to cancel again
        with pytest.raises(ValueError):
            OrderService.cancel_order(order.id, customer_user.id)

    def test_update_order_status_all_transitions(self, app, customer_user, product, seller_user):
        """Test all valid order status transitions"""
        from app.enums import OrderStatus
        
        order = OrderService.create_order(
            customer_id=customer_user.id,
            items_data=[{"product_id": product.id, "quantity": 1}],
            shipping_address="123 Test St",
            shipping_phone="0901234567",
        )

        # Pending -> Confirmed
        order = OrderService.update_order_status(order.id, seller_user.id, OrderStatus.CONFIRMED)
        assert order.status == OrderStatus.CONFIRMED

        # Confirmed -> Shipping
        order = OrderService.update_order_status(order.id, seller_user.id, OrderStatus.SHIPPING)
        assert order.status == OrderStatus.SHIPPING

        # Shipping -> Completed
        order = OrderService.update_order_status(order.id, seller_user.id, OrderStatus.COMPLETED)
        assert order.status == OrderStatus.COMPLETED
