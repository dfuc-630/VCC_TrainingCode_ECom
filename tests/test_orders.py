import pytest
from decimal import Decimal
from app.extensions import db
from app.models.order import Order, OrderItem
from app.enums import OrderStatus, PaymentStatus


class TestOrderModelExtended:
    """Test Order model extended functionality"""

    def test_order_calculate_total(self, app, customer_user, product):
        """Test order calculate_total method"""
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

        item1 = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            price=product.current_price,
            quantity=2,
            subtotal=product.current_price * 2,
        )
        item2 = OrderItem(
            order_id=order.id,
            product_id=product.id,
            product_name=product.name,
            price=product.current_price,
            quantity=1,
            subtotal=product.current_price * 1,
        )
        db.session.add(item1)
        db.session.add(item2)
        db.session.commit()

        total = order.calculate_total()
        assert total == product.current_price * 3

    def test_order_can_cancel_pending(self, app, customer_user, product):
        """Test can_cancel for pending order"""
        order = Order(
            order_number="TEST001",
            customer_id=customer_user.id,
            seller_id=product.seller_id,
            total_amount=Decimal("100000.00"),
            status=OrderStatus.PENDING,
            shipping_address="Test",
            shipping_phone="123",
        )
        assert order.can_cancel() is True

    def test_order_can_cancel_confirmed(self, app, customer_user, product):
        """Test can_cancel for confirmed order"""
        order = Order(
            order_number="TEST001",
            customer_id=customer_user.id,
            seller_id=product.seller_id,
            total_amount=Decimal("100000.00"),
            status=OrderStatus.CONFIRMED,
            shipping_address="Test",
            shipping_phone="123",
        )
        assert order.can_cancel() is True

    def test_order_cannot_cancel_shipping(self, app, customer_user, product):
        """Test cannot cancel shipping order"""
        order = Order(
            order_number="TEST001",
            customer_id=customer_user.id,
            seller_id=product.seller_id,
            total_amount=Decimal("100000.00"),
            status=OrderStatus.SHIPPING,
            shipping_address="Test",
            shipping_phone="123",
        )
        assert order.can_cancel() is False

    def test_order_cannot_cancel_completed(self, app, customer_user, product):
        """Test cannot cancel completed order"""
        order = Order(
            order_number="TEST001",
            customer_id=customer_user.id,
            seller_id=product.seller_id,
            total_amount=Decimal("100000.00"),
            status=OrderStatus.COMPLETED,
            shipping_address="Test",
            shipping_phone="123",
        )
        assert order.can_cancel() is False

    def test_order_to_dict_with_items(self, app, customer_user, product):
        """Test order to_dict with items"""
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
            quantity=1,
            subtotal=product.current_price,
        )
        db.session.add(item)
        db.session.commit()

        data = order.to_dict(include_items=True)
        assert "items" in data
        assert len(data["items"]) == 1

    def test_order_to_dict_without_items(self, app, customer_user, product):
        """Test order to_dict without items"""
        order = Order(
            order_number="TEST001",
            customer_id=customer_user.id,
            seller_id=product.seller_id,
            total_amount=Decimal("100000.00"),
            shipping_address="Test",
            shipping_phone="123",
        )
        db.session.add(order)
        db.session.commit()

        data = order.to_dict(include_items=False)
        assert "items" not in data
