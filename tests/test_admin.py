import pytest


class TestAdminUsers:
    """Test admin user management"""

    def test_get_users_success(self, client, admin_headers, customer_user, seller_user):
        """Test get all users"""
        response = client.get("/api/admin/users", headers=admin_headers)

        assert response.status_code == 200
        assert "users" in response.json
        assert len(response.json["users"]) >= 2  # At least customer and seller

    def test_get_users_filter_by_role(
        self, client, admin_headers, customer_user, seller_user
    ):
        """Test get users filtered by role"""
        response = client.get("/api/admin/users?role=customer", headers=admin_headers)

        assert response.status_code == 200
        assert all(u["role"] == "customer" for u in response.json["users"])

    def test_get_users_unauthorized(self, client, customer_headers):
        """Test get users as non-admin (should fail)"""
        response = client.get("/api/admin/users", headers=customer_headers)

        assert response.status_code == 403

    def test_get_user_detail_success(self, client, admin_headers, customer_user):
        """Test get user detail"""
        response = client.get(
            f"/api/admin/users/{customer_user.id}", headers=admin_headers
        )

        assert response.status_code == 200
        assert "user" in response.json
        assert response.json["user"]["username"] == "customer"

    def test_get_user_not_found(self, client, admin_headers):
        """Test get non-existent user"""
        response = client.get("/api/admin/users/invalid-id", headers=admin_headers)

        assert response.status_code == 404


class TestAdminProducts:
    """Test admin product management"""

    def test_get_products_success(self, client, admin_headers, product):
        """Test get all products"""
        response = client.get("/api/admin/products", headers=admin_headers)

        assert response.status_code == 200
        assert "products" in response.json
        assert len(response.json["products"]) == 1

    def test_get_products_filter_by_seller(
        self, client, admin_headers, product, seller_user
    ):
        """Test get products filtered by seller"""
        response = client.get(
            f"/api/admin/products?seller_id={seller_user.id}", headers=admin_headers
        )

        assert response.status_code == 200
        assert all(p["seller_id"] == seller_user.id for p in response.json["products"])

    def test_get_product_detail_success(self, client, admin_headers, product):
        """Test get product detail"""
        response = client.get(
            f"/api/admin/products/{product.id}", headers=admin_headers
        )

        assert response.status_code == 200
        assert "product" in response.json


class TestAdminOrders:
    """Test admin order management"""

    def test_get_orders_success(self, client, admin_headers, customer_headers, product):
        """Test get all orders"""
        # Create order
        client.post(
            "/api/customer/orders",
            headers=customer_headers,
            json={
                "items": [{"product_id": product.id, "quantity": 1}],
                "shipping_address": "123 Test St",
                "shipping_phone": "0901234567",
            },
        )

        # Get orders as admin
        response = client.get("/api/admin/orders", headers=admin_headers)

        assert response.status_code == 200
        assert "orders" in response.json
        assert len(response.json["orders"]) == 1

    def test_get_orders_filter_by_status(self, client, admin_headers):
        """Test get orders filtered by status"""
        response = client.get("/api/admin/orders?status=pending", headers=admin_headers)

        assert response.status_code == 200

    def test_get_order_detail_success(
        self, client, admin_headers, customer_headers, product
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

        # Get detail as admin
        response = client.get(f"/api/admin/orders/{order_id}", headers=admin_headers)

        assert response.status_code == 200
        assert "order" in response.json


class TestAdminDashboard:
    """Test admin dashboard"""

    def test_get_dashboard_success(
        self, client, admin_headers, customer_user, seller_user, product
    ):
        """Test get dashboard statistics"""
        response = client.get("/api/admin/dashboard", headers=admin_headers)

        assert response.status_code == 200
        assert "users" in response.json
        assert "products" in response.json
        assert "orders" in response.json
        assert "revenue" in response.json

        assert response.json["users"]["total"] >= 2
        assert response.json["products"]["total"] >= 1

    def test_get_dashboard_unauthorized(self, client, customer_headers):
        """Test get dashboard as non-admin"""
        response = client.get("/api/admin/dashboard", headers=customer_headers)

        assert response.status_code == 403
