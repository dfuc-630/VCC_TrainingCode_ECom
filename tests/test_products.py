import pytest
from decimal import Decimal
from app.extensions import db
from app.models.product import Product


class TestProductModelExtended:
    """Test Product model extended functionality"""

    def test_product_add_stock(self, app, product):
        """Test add stock to product"""
        initial_stock = product.stock_quantity
        product.add_stock(5)
        db.session.commit()

        assert product.stock_quantity == initial_stock + 5

    def test_product_deduct_stock_insufficient(self, app, product):
        """Test deduct stock with insufficient quantity"""
        product.stock_quantity = 1
        db.session.commit()

        with pytest.raises(ValueError, match="Insufficient stock"):
            product.deduct_stock(5)

    def test_product_version_increment(self, app, product):
        """Test version increment on stock change"""
        initial_version = product.version
        product.deduct_stock(1)
        db.session.commit()

        assert product.version == initial_version + 1

        product.add_stock(1)
        db.session.commit()

        assert product.version == initial_version + 2

    def test_product_to_dict(self, app, product):
        """Test product to_dict"""
        data = product.to_dict()
        assert "current_price" in data
        assert isinstance(data["current_price"], float)
        assert "original_price" in data

    def test_product_to_dict_without_original_price(self, app, seller_user, category):
        """Test product to_dict without original_price"""
        product = Product(
            seller_id=seller_user.id,
            category_id=category.id,
            name="Test Product",
            slug="test-product",
            current_price=Decimal("100000.00"),
            stock_quantity=10,
        )
        db.session.add(product)
        db.session.commit()

        data = product.to_dict()
        assert data["original_price"] is None
