import pytest
from decimal import Decimal
from app.services.auth_service import AuthService
from app.services.wallet_service import WalletService
from app.services.product_service import ProductService
from app.services.order_service import OrderService


class TestAuthService:
    """Test authentication service"""

    def test_register_user_success(self, app):
        """Test user registration"""
        user = AuthService.register_user(
            email="service@test.com",
            username="serviceuser",
            password="password123",
            role="customer",
            full_name="Service Test",
        )

        assert user.email == "service@test.com"
        assert user.role == "customer"
        assert user.check_password("password123")

    def test_register_duplicate_email(self, app, customer_user):
        """Test registration with duplicate email"""
        with pytest.raises(ValueError, match="Email already exists"):
            AuthService.register_user(
                email="customer@test.com",
                username="different",
                password="password123",
                role="customer",
            )

    def test_login_success(self, app, customer_user):
        """Test user login"""
        result = AuthService.login_user("customer", "password123")

        assert "access_token" in result
        assert "refresh_token" in result
        assert "user" in result

    def test_login_invalid_credentials(self, app):
        """Test login with invalid credentials"""
        with pytest.raises(ValueError, match="Invalid credentials"):
            AuthService.login_user("nonexistent", "password")


class TestWalletService:
    """Test wallet service"""

    def test_deposit_success(self, app, customer_user):
        """Test deposit to wallet"""
        wallet = WalletService.get_wallet_by_user_id(customer_user.id)
        initial_balance = wallet.balance

        wallet, transaction = WalletService.deposit(
            wallet.id, Decimal("500000.00"), "Test deposit"
        )

        assert wallet.balance == initial_balance + Decimal("500000.00")
        assert transaction.type == "deposit"
        assert transaction.amount == Decimal("500000.00")

    def test_deduct_success(self, app, customer_user):
        """Test deduct from wallet"""
        wallet = WalletService.get_wallet_by_user_id(customer_user.id)
        initial_balance = wallet.balance

        transaction = WalletService.deduct(
            wallet.id, Decimal("100000.00"), description="Test payment"
        )

        assert wallet.balance == initial_balance - Decimal("100000.00")
        assert transaction.type == "payment"

    def test_deduct_insufficient_balance(self, app, customer_user):
        """Test deduct with insufficient balance"""
        from app.models.wallet import Wallet

        wallet = Wallet.query.filter_by(user_id=customer_user.id).first()
        wallet.balance = Decimal("1000.00")
        db.session.commit()

        with pytest.raises(ValueError, match="Insufficient balance"):
            WalletService.deduct(wallet.id, Decimal("100000.00"))


class TestProductService:
    """Test product service"""

    def test_create_product_success(self, app, seller_user, category):
        """Test create product"""
        product = ProductService.create_product(
            seller_id=seller_user.id,
            name="Test Product",
            current_price=Decimal("100000.00"),
            category_id=category.id,
            stock_quantity=10,
        )

        assert product.name == "Test Product"
        assert product.slug == "test-product"
        assert product.seller_id == seller_user.id

    def test_create_product_unique_slug(self, app, seller_user):
        """Test unique slug generation"""
        product1 = ProductService.create_product(
            seller_id=seller_user.id,
            name="Test Product",
            current_price=Decimal("100000.00"),
        )

        product2 = ProductService.create_product(
            seller_id=seller_user.id,
            name="Test Product",
            current_price=Decimal("200000.00"),
        )

        assert product1.slug == "test-product"
        assert product2.slug == "test-product-1"

    def test_update_product_success(self, app, product, seller_user):
        """Test update product"""
        updated = ProductService.update_product(
            product.id,
            seller_user.id,
            name="Updated Product",
            current_price=Decimal("25000000.00"),
        )

        assert updated.name == "Updated Product"
        assert updated.current_price == Decimal("25000000.00")

    def test_delete_product_success(self, app, product, seller_user):
        """Test delete product"""
        ProductService.delete_product(product.id, seller_user.id)

        from app.models.product import Product

        deleted = Product.query.get(product.id)
        assert deleted.is_deleted is True


class TestOrderService:
    """Test order service"""

    def test_create_order_success(self, app, customer_user, product):
        """Test create order"""
        items_data = [{"product_id": product.id, "quantity": 2}]

        order = OrderService.create_order(
            customer_id=customer_user.id,
            items_data=items_data,
            shipping_address="123 Test St",
            shipping_phone="0901234567",
        )

        assert order.customer_id == customer_user.id
        assert order.total_amount == product.current_price * 2
        assert order.status == "pending"
        assert order.payment_status == "paid"

    def test_create_order_deducts_stock(self, app, customer_user, product):
        """Test order creation deducts stock"""
        initial_stock = product.stock_quantity

        OrderService.create_order(
            customer_id=customer_user.id,
            items_data=[{"product_id": product.id, "quantity": 2}],
            shipping_address="123 Test St",
            shipping_phone="0901234567",
        )

        db.session.refresh(product)
        assert product.stock_quantity == initial_stock - 2

    def test_create_order_insufficient_stock(self, app, customer_user, product):
        """Test order with insufficient stock"""
        with pytest.raises(ValueError, match="Insufficient stock"):
            OrderService.create_order(
                customer_id=customer_user.id,
                items_data=[{"product_id": product.id, "quantity": 100}],
                shipping_address="123 Test St",
                shipping_phone="0901234567",
            )

    def test_cancel_order_refunds(self, app, customer_user, product):
        """Test order cancellation refunds money"""
        from app.models.wallet import Wallet

        wallet = Wallet.query.filter_by(user_id=customer_user.id).first()
        initial_balance = wallet.balance

        # Create order
        order = OrderService.create_order(
            customer_id=customer_user.id,
            items_data=[{"product_id": product.id, "quantity": 1}],
            shipping_address="123 Test St",
            shipping_phone="0901234567",
        )

        # Cancel order
        OrderService.cancel_order(order.id, customer_user.id)

        db.session.refresh(wallet)
        assert wallet.balance == initial_balance
        assert order.status == "cancelled"
        assert order.payment_status == "refunded"
