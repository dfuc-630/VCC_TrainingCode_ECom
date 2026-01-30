import pytest
from decimal import Decimal
from app.extensions import db


class TestUserModel:
    """Test User model"""

    def test_set_password(self, app):
        """Test password hashing"""
        from app.models.user import User

        user = User(username="test", email="test@test.com", role="customer")
        user.set_password("password123")

        assert user.password_hash != "password123"
        assert user.check_password("password123")

    def test_check_password(self, app, customer_user):
        """Test password verification"""
        assert customer_user.check_password("password123")
        assert not customer_user.check_password("wrongpassword")

    def test_has_role(self, app, customer_user, seller_user):
        """Test role checking"""
        assert customer_user.has_role("customer")
        assert not customer_user.has_role("seller")
        assert seller_user.has_role("seller")

    def test_to_dict_excludes_password(self, app, customer_user):
        """Test to_dict excludes sensitive data"""
        data = customer_user.to_dict()
        assert "password_hash" not in data
        assert "email" in data


class TestWalletModel:
    """Test Wallet model"""

    def test_can_deduct(self, app, customer_user):
        """Test can_deduct method"""
        from app.models.wallet import Wallet

        wallet = Wallet.query.filter_by(user_id=customer_user.id).first()

        assert wallet.can_deduct(Decimal("100000.00"))
        assert not wallet.can_deduct(Decimal("1000000000.00"))

    def test_add_balance(self, app, customer_user):
        """Test add_balance method"""
        from app.models.wallet import Wallet

        wallet = Wallet.query.filter_by(user_id=customer_user.id).first()
        initial = wallet.balance

        wallet.add_balance(Decimal("500000.00"))
        db.session.commit()

        assert wallet.balance == initial + Decimal("500000.00")

    def test_deduct_balance(self, app, customer_user):
        """Test deduct_balance method"""
        from app.models.wallet import Wallet

        wallet = Wallet.query.filter_by(user_id=customer_user.id).first()
        initial = wallet.balance

        wallet.deduct_balance(Decimal("100000.00"))
        db.session.commit()

        assert wallet.balance == initial - Decimal("100000.00")


class TestProductModel:
    """Test Product model"""

    def test_has_stock(self, app, product):
        """Test has_stock method"""
        assert product.has_stock(5)
        assert not product.has_stock(100)

    def test_deduct_stock(self, app, product):
        """Test deduct_stock method"""
        initial = product.stock_quantity
        product.deduct_stock(2)
        db.session.commit()

        assert product.stock_quantity == initial - 2

    def test_soft_delete(self, app, product):
        """Test soft delete"""
        product.soft_delete()

        assert product.is_deleted is True
        assert product.deleted_at is not None


class TestOrderModel:
    """Test Order model"""

    def test_calculate_total(self, app, customer_user, product):
        """Test calculate_total method"""
        from app.models.order import Order, OrderItem

        order = Order(
            order_number="TEST001",
            customer_id=customer_user.id,
            seller_id=product.seller_id,
            total_amount=Decimal("0"),
            shipping_address="Test",
            shipping_phone="123",
        )
        db.session.add(order)
        db.session.flush()

        item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            price=product.current_price,
            quantity=2,
            subtotal=product.current_price * 2,
        )
        db.session.add(item)
        db.session.commit()

        total = order.calculate_total()
        assert total == product.current_price * 2

    def test_can_cancel(self, app):
        """Test can_cancel method"""
        from app.models.order import Order

        order_pending = Order(
            status="pending",
            order_number="TEST",
            customer_id="1",
            seller_id="2",
            total_amount=Decimal("100"),
        )
        order_completed = Order(
            status="completed",
            order_number="TEST2",
            customer_id="1",
            seller_id="2",
            total_amount=Decimal("100"),
        )

        assert order_pending.can_cancel()
        assert not order_completed.can_cancel()
