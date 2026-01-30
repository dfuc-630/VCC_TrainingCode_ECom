import pytest


class TestSellerOrders:
    """Test seller order management"""

    def test_get_orders_success(
        self, client, seller_headers, customer_headers, product
    ):
        """Test get seller's orders"""
        # Create order as customer
        client.post(
            "/api/v1/customer/orders",
            headers=customer_headers,
            json={
                "items": [{"product_id": product.id, "quantity": 1}],
                "shipping_address": "123 Test St",
                "shipping_phone": "0901234567",
            },
        )

        # Get orders as seller
        response = client.get("/api/v1/seller/orders", headers=seller_headers)

        assert response.status_code == 200
        assert "orders" in response.json
        assert len(response.json["orders"]) == 1

    def test_get_order_detail_success(
        self, client, seller_headers, customer_headers, product
    ):
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

        # Get detail as seller
        response = client.get(f"/api/v1/seller/orders/{order_id}", headers=seller_headers)

        assert response.status_code == 200
        assert "order" in response.json
        assert "items" in response.json["order"]

    def test_update_order_status_success(
        self, client, seller_headers, customer_headers, product
    ):
        """Test update order status"""
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

        # Update status to confirmed
        response = client.put(
            f"/api/v1/seller/orders/{order_id}/status",
            headers=seller_headers,
            json={"status": "confirmed"},
        )

        assert response.status_code == 200
        assert response.json["order"]["status"] == "confirmed"

    def test_update_order_status_invalid_transition(
        self, client, seller_headers, customer_headers, product
    ):
        """Test invalid status transition"""
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

        # Try invalid transition (pending -> completed)
        response = client.put(
            f"/api/v1/seller/orders/{order_id}/status",
            headers=seller_headers,
            json={"status": "completed"},
        )

        assert response.status_code == 400

    def test_update_order_status_wrong_seller(
        self, client, seller_headers, customer_headers, product
    ):
        """Test update order status as wrong seller"""
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

        # Try to update as customer (should fail)
        response = client.put(
            f"/api/v1/seller/orders/{order_id}/status",
            headers=customer_headers,
            json={"status": "confirmed"},
        )

        assert response.status_code == 403

    def test_update_order_status_missing_status(
        self, client, seller_headers, customer_headers, product
    ):
        """Test update order status without status field"""
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

        # Update without status
        response = client.put(
            f"/api/v1/seller/orders/{order_id}/status",
            headers=seller_headers,
            json={},
        )

        assert response.status_code == 400

    def test_get_orders_filter_by_status(
        self, client, seller_headers, customer_headers, product
    ):
        """Test get orders filtered by status"""
        # Create order
        client.post(
            "/api/v1/customer/orders",
            headers=customer_headers,
            json={
                "items": [{"product_id": product.id, "quantity": 1}],
                "shipping_address": "123 Test St",
                "shipping_phone": "0901234567",
            },
        )

        # Get pending orders
        response = client.get(
            "/api/v1/seller/orders?status=pending", headers=seller_headers
        )

        assert response.status_code == 200
        assert "orders" in response.json