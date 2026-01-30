import pytest
from decimal import Decimal
from app.extensions import db
from app.models.category import Category
from app.models.order import OrderItem
from app.models.wallet import WalletTransaction
from app.enums import TransactionType


class TestCategoryModel:
    """Test Category model"""

    def test_create_category(self, app):
        """Test create category"""
        category = Category(
            name="Electronics",
            slug="electronics",
            description="Electronic devices",
        )
        db.session.add(category)
        db.session.commit()

        assert category.name == "Electronics"
        assert category.slug == "electronics"

    def test_category_products_relationship(self, app, category, product):
        """Test category products relationship"""
        assert product.category_id == category.id
        assert product in category.products.all()


class TestOrderItemModel:
    """Test OrderItem model"""

    def test_create_order_item(self, app, customer_user, product):
        """Test create order item"""
        from app.models.order import Order

        order = Order(
            order_number="TEST001",
            customer_id=customer_user.id,
            seller_id=product.seller_id,
            total_amount=Decimal("100000.00"),
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

        assert item.order_id == order.id
        assert item.product_id == product.id
        assert item.quantity == 2

    def test_calculate_subtotal(self, app):
        """Test calculate subtotal"""
        item = OrderItem(
            price=Decimal("100000.00"),
            quantity=3,
        )
        subtotal = item.calculate_subtotal()
        assert subtotal == Decimal("300000.00")

    def test_to_dict(self, app, customer_user, product):
        """Test order item to_dict"""
        from app.models.order import Order

        order = Order(
            order_number="TEST001",
            customer_id=customer_user.id,
            seller_id=product.seller_id,
            total_amount=Decimal("100000.00"),
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

        data = item.to_dict()
        assert "price" in data
        assert "subtotal" in data
        assert isinstance(data["price"], float)
        assert isinstance(data["subtotal"], float)


class TestWalletTransactionModel:
    """Test WalletTransaction model"""

    def test_create_transaction(self, app, customer_user):
        """Test create wallet transaction"""
        from app.models.wallet import Wallet

        wallet = Wallet.query.filter_by(user_id=customer_user.id).first()

        transaction = WalletTransaction(
            wallet_id=wallet.id,
            type=TransactionType.DEPOSIT,
            amount=Decimal("500000.00"),
            balance_before=Decimal("1000000.00"),
            balance_after=Decimal("1500000.00"),
            description="Test deposit",
        )
        db.session.add(transaction)
        db.session.commit()

        assert transaction.type == TransactionType.DEPOSIT
        assert transaction.amount == Decimal("500000.00")

    def test_transaction_to_dict(self, app, customer_user):
        """Test transaction to_dict"""
        from app.models.wallet import Wallet

        wallet = Wallet.query.filter_by(user_id=customer_user.id).first()

        transaction = WalletTransaction(
            wallet_id=wallet.id,
            type=TransactionType.DEPOSIT,
            amount=Decimal("500000.00"),
            balance_before=Decimal("1000000.00"),
            balance_after=Decimal("1500000.00"),
        )
        db.session.add(transaction)
        db.session.commit()

        data = transaction.to_dict()
        assert "amount" in data
        assert "balance_before" in data
        assert "balance_after" in data
        assert isinstance(data["amount"], float)
        assert isinstance(data["balance_before"], float)
        assert isinstance(data["balance_after"], float)
