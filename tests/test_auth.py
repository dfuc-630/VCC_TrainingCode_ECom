import pytest, db


class TestAuthRegistration:
    """Test user registration"""

    def test_register_customer_success(self, client):
        """Test successful customer registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newcustomer@test.com",
                "username": "newcustomer",
                "password": "password123",
                "full_name": "New Customer",
                "phone": "0909999999",
                "role": "customer",
            },
        )

        assert response.status_code == 201
        assert "user" in response.json
        assert response.json["user"]["email"] == "newcustomer@test.com"
        assert response.json["user"]["role"] == "customer"
        assert "password_hash" not in response.json["user"]

    def test_register_seller_success(self, client):
        """Test successful seller registration"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "newseller@test.com",
                "username": "newseller",
                "password": "password123",
                "role": "seller",
            },
        )

        assert response.status_code == 201
        assert response.json["user"]["role"] == "seller"

    def test_register_duplicate_email(self, client, customer_user):
        """Test registration with duplicate email"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "customer@test.com",
                "username": "different",
                "password": "password123",
                "role": "customer",
            },
        )

        assert response.status_code == 400
        assert "Email already exists" in response.json["error"]

    def test_register_duplicate_username(self, client, customer_user):
        """Test registration with duplicate username"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "different@test.com",
                "username": "customer",
                "password": "password123",
                "role": "customer",
            },
        )

        assert response.status_code == 400
        assert "Username already exists" in response.json["error"]

    def test_register_invalid_role(self, client):
        """Test registration with invalid role"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "test@test.com",
                "username": "test",
                "password": "password123",
                "role": "superadmin",
            },
        )

        assert response.status_code == 400

    def test_register_missing_fields(self, client):
        """Test registration with missing required fields"""
        response = client.post(
            "/api/auth/register",
            json={"email": "test@test.com", "password": "password123"},
        )

        assert response.status_code == 400

    def test_register_invalid_email(self, client):
        """Test registration with invalid email format"""
        response = client.post(
            "/api/auth/register",
            json={
                "email": "invalid-email",
                "username": "test",
                "password": "password123",
                "role": "customer",
            },
        )

        assert response.status_code == 400


class TestAuthLogin:
    """Test user login"""

    def test_login_success(self, client, customer_user):
        """Test successful login"""
        response = client.post(
            "/api/auth/login", json={"username": "customer", "password": "password123"}
        )

        assert response.status_code == 200
        assert "access_token" in response.json
        assert "refresh_token" in response.json
        assert "user" in response.json
        assert response.json["user"]["username"] == "customer"

    def test_login_invalid_username(self, client):
        """Test login with invalid username"""
        response = client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "password123"},
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json["error"]

    def test_login_invalid_password(self, client, customer_user):
        """Test login with invalid password"""
        response = client.post(
            "/api/auth/login",
            json={"username": "customer", "password": "wrongpassword"},
        )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json["error"]

    def test_login_inactive_user(self, client, customer_user):
        """Test login with inactive user"""
        customer_user.is_active = False
        db.session.commit()

        response = client.post(
            "/api/auth/login", json={"username": "customer", "password": "password123"}
        )

        assert response.status_code == 403


class TestAuthToken:
    """Test token operations"""

    def test_refresh_token(self, client, customer_user):
        """Test refresh token"""
        # Login to get refresh token
        login_response = client.post(
            "/api/auth/login", json={"username": "customer", "password": "password123"}
        )
        refresh_token = login_response.json["refresh_token"]

        # Refresh
        response = client.post(
            "/api/auth/refresh", headers={"Authorization": f"Bearer {refresh_token}"}
        )

        assert response.status_code == 200
        assert "access_token" in response.json

    def test_get_me_success(self, client, customer_headers):
        """Test get current user"""
        response = client.get("/api/auth/me", headers=customer_headers)

        assert response.status_code == 200
        assert "user" in response.json
        assert response.json["user"]["username"] == "customer"

    def test_get_me_without_token(self, client):
        """Test get current user without token"""
        response = client.get("/api/auth/me")

        assert response.status_code == 401

    def test_get_me_invalid_token(self, client):
        """Test get current user with invalid token"""
        response = client.get(
            "/api/auth/me", headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 422
