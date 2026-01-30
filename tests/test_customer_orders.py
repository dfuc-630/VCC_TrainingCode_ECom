import pytest
from decimal import Decimal
from app.extensions import db


class TestCustomerOrders:
    """Test customer order operations"""

    def test_create_order_success(self, client, customer_headers, product):
        """Test successful order creation"""
        response = client.post(
            "/api/v1/customer/orders",
            headers=customer_headers,
            json={
                "items": [{"product_id": product.id, "quantity": 2}],
                "shipping_address": "123 Test St, Hanoi",
                "shipping_phone": "0901234567",
            },
        )

        assert response.status_code == 201
        assert "order" in response.json
        assert response.json["order"]["total_amount"] == 59980000.00
        assert response.json["order"]["status"] == "pending"
        assert response.json["order"]["payment_status"] == "paid"
        assert len(response.json["order"]["items"]) == 1

    def test_create_order_insufficient_balance(
        self, client, customer_user, customer_headers, product
    ):
        """Test order creation with insufficient balance"""
        # Reduce wallet balance
        from app.models.wallet import Wallet

        wallet = Wallet.query.filter_by(user_id=customer_user.id).first()
        wallet.balance = Decimal("1000.00")
        db.session.commit()

        response = client.post(
            "/api/v1/customer/orders",
            headers=customer_headers,
            json={
                "items": [{"product_id": product.id, "quantity": 1}],
                "shipping_address": "123 Test St",
                "shipping_phone": "0901234567",
            },
        )

        assert response.status_code == 400
        assert "Insufficient balance" in response.json["error"]

    def test_create_order_insufficient_stock(self, client, customer_headers, product):
        """Test order creation with insufficient stock"""
        response = client.post(
            "/api/v1/customer/orders",
            headers=customer_headers,
            json={
                "items": [{"product_id": product.id, "quantity": 100}],
                "shipping_address": "123 Test St",
                "shipping_phone": "0901234567",
            },
        )

        assert response.status_code == 400
        assert "Insufficient stock" in response.json["error"]

    def test_create_order_product_not_found(self, client, customer_headers):
        """Test order creation with non-existent product"""
        response = client.post(
            "/api/v1/customer/orders",
            headers=customer_headers,
            json={
                "items": [{"product_id": "invalid-id", "quantity": 1}],
                "shipping_address": "123 Test St",
                "shipping_phone": "0901234567",
            },
        )

        assert response.status_code == 400

    def test_create_order_empty_items(self, client, customer_headers):
        """Test order creation with empty items"""
        response = client.post(
            "/api/v1/customer/orders",
            headers=customer_headers,
            json={
                "items": [],
                "shipping_address": "123 Test St",
                "shipping_phone": "0901234567",
            },
        )

        assert response.status_code == 400

    def test_create_order_missing_fields(self, client, customer_headers, product):
        """Test order creation with missing fields"""
        response = client.post(
            "/api/v1/customer/orders",
            headers=customer_headers,
            json={"items": [{"product_id": product.id, "quantity": 1}]},
        )

        assert response.status_code == 400

    def test_get_orders_success(self, client, customer_headers, product):
        """Test get customer orders"""
        # Create an order first
        client.post(
            "/api/v1/customer/orders",
            headers=customer_headers,
            json={
                "items": [{"product_id": product.id, "quantity": 1}],
                "shipping_address": "123 Test St",
                "shipping_phone": "0901234567",
            },
        )

        response = client.get("/api/v1/customer/orders", headers=customer_headers)

        assert response.status_code == 200
        assert "orders" in response.json
        assert len(response.json["orders"]) == 1

    def test_get_orders_filter_by_status(self, client, customer_headers, product):
        """Test get orders filtered by status"""
        response = client.get(
            "/api/v1/customer/orders?status=pending", headers=customer_headers
        )

        assert response.status_code == 200

    def test_get_order_detail_success(self, client, customer_headers, product):
        """Test get order detail"""
        # Create order
        create_response = client.post(
            "/api/v1/customer/orders",
            headers=customer_headers,
            json={
                "items": [{"product_id": product.id, "quantity": 1}],
                "shipping_address": "123 Test St",
                "shipping_phone": "0901234567",
            },
        )
        order_id = create_response.json["order"]["id"]

        # Get order detail
        response = client.get(
            f"/api/v1/customer/orders/{order_id}",
            headers=customer_headers,
        )

        assert response.status_code == 200
        assert response.json["order"]["status"] == "pending"

    def test_cancel_order_success(self, client, customer_headers, product):
        """Test successful order cancellation"""
        # Create order
        create_response = client.post(
            "/api/v1/customer/orders",
            headers=customer_headers,
            json={
                "items": [{"product_id": product.id, "quantity": 1}],
                "shipping_address": "123 Test St",
                "shipping_phone": "0901234567",
            },
        )
        order_id = create_response.json["order"]["id"]

        # Cancel order
        response = client.put(
            f"/api/v1/customer/orders/{order_id}/cancel",
            headers=customer_headers,
        )

        assert response.status_code == 200
        assert response.json["order"]["status"] == "cancelled"
        assert response.json["order"]["payment_status"] == "refunded"

    def test_cancel_order_not_found(self, client, customer_headers):
        """Test cancel non-existent order"""
        response = client.put(
            "/api/v1/customer/orders/invalid-id/cancel",
            headers=customer_headers,
        )

        assert response.status_code == 400

    def test_cancel_order_wrong_customer(self, client, customer_headers, seller_headers, product):
        """Test cancel order as wrong customer"""
        # Create order as customer
        create_response = client.post(
            "/api/v1/customer/orders",
            headers=customer_headers,
            json={
                "items": [{"product_id": product.id, "quantity": 1}],
                "shipping_address": "123 Test St",
                "shipping_phone": "0901234567",
            },
        )
        order_id = create_response.json["order"]["id"]

        # Try to cancel as seller (should fail)
        response = client.put(
            f"/api/v1/customer/orders/{order_id}/cancel",
            headers=seller_headers,
        )

        assert response.status_code == 403
