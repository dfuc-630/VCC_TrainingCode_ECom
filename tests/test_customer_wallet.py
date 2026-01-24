import pytest
from decimal import Decimal


class TestCustomerWallet:
    """Test customer wallet operations"""

    def test_get_wallet_success(self, client, customer_headers):
        """Test get wallet balance"""
        response = client.get("/api/customer/wallet", headers=customer_headers)

        assert response.status_code == 200
        assert "wallet" in response.json
        assert "balance" in response.json["wallet"]
        assert response.json["wallet"]["balance"] == 1000000.00

    def test_get_wallet_unauthorized(self, client):
        """Test get wallet without authentication"""
        response = client.get("/api/customer/wallet")

        assert response.status_code == 401

    def test_get_wallet_wrong_role(self, client, seller_headers):
        """Test get wallet as seller (should fail)"""
        response = client.get("/api/customer/wallet", headers=seller_headers)

        assert response.status_code == 403

    def test_deposit_success(self, client, customer_headers, customer_user):
        """Test successful deposit"""
        response = client.post(
            "/api/customer/wallet/deposit",
            headers=customer_headers,
            json={"amount": 500000.00, "description": "Test deposit"},
        )

        assert response.status_code == 200
        assert "wallet" in response.json
        assert "transaction" in response.json
        assert response.json["wallet"]["balance"] == 1500000.00
        assert response.json["transaction"]["amount"] == 500000.00
        assert response.json["transaction"]["type"] == "deposit"

    def test_deposit_invalid_amount(self, client, customer_headers):
        """Test deposit with invalid amount"""
        response = client.post(
            "/api/customer/wallet/deposit",
            headers=customer_headers,
            json={"amount": -100.00},
        )

        assert response.status_code == 400

    def test_deposit_missing_amount(self, client, customer_headers):
        """Test deposit without amount"""
        response = client.post(
            "/api/customer/wallet/deposit", headers=customer_headers, json={}
        )

        assert response.status_code == 400

    def test_get_transactions_success(self, client, customer_headers):
        """Test get wallet transactions"""
        # Make some deposits first
        client.post(
            "/api/customer/wallet/deposit",
            headers=customer_headers,
            json={"amount": 100000.00},
        )
        client.post(
            "/api/customer/wallet/deposit",
            headers=customer_headers,
            json={"amount": 200000.00},
        )

        response = client.get(
            "/api/customer/wallet/transactions", headers=customer_headers
        )

        assert response.status_code == 200
        assert "transactions" in response.json
        assert len(response.json["transactions"]) == 2
        assert "total" in response.json

    def test_get_transactions_pagination(self, client, customer_headers):
        """Test transactions pagination"""
        response = client.get(
            "/api/customer/wallet/transactions?page=1&per_page=5",
            headers=customer_headers,
        )

        assert response.status_code == 200
        assert response.json["page"] == 1
