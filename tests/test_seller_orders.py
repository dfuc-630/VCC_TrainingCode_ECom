import pytest


class TestSellerOrders:
    """Test seller order management"""

    def test_get_orders_success(
        self, client, seller_headers, customer_headers, product
    ):
        """Test get seller's orders"""
        # Create order as customer
        client.post(
            "/api/customer/orders",
            headers=customer_headers,
            json={
                "items": [{"product_id": product.id, "quantity": 1}],
                "shipping_address": "123 Test St",
                "shipping_phone": "0901234567",
            },
        )

        # Get orders as seller
        response = client.get("/api/seller/orders", headers=seller_headers)

        assert response.status_code == 200
        assert "orders" in response.json
        assert len(response.json["orders"]) == 1

    def test_get_order_detail_success(
        self, client, seller_headers, customer_headers, product
    ):
        """Test get order detail"""
        # Create order
        create_response = client.post(
            "/api/customer/orders",
            headers=customer_headers,
            json={
                "items": [{"product_id": product.id, "quantity": 1}],
                "shipping_address": "123 Test St",
                "shipping_phone": "0901234567",
            },
        )
        order_id = create_response.json["order"]["id"]

        # Get detail as seller
        response = client.get(f"/api/seller/orders/{order_id}", headers=seller_headers)

        assert response.status_code == 200
        assert "order" in response.json
        assert "items" in response.json["order"]

    def test_update_order_status_success(
        self, client, seller_headers, customer_headers, product
    ):
        """Test update order status"""
        # Create order
        create_response = client.post(
            "/api/customer/orders",
            headers=customer_headers,
            json={
                "items": [{"product_id": product.id, "quantity": 1}],
            },
        )
