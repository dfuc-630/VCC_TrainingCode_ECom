import pytest
from app.extensions import db


class TestAdminUserManagement:
    """Test admin user management endpoints"""

    def test_update_user_success(self, client, admin_headers, customer_user):
        """Test update user information"""
        response = client.put(
            f"/api/v1/admin/users/{customer_user.id}",
            headers=admin_headers,
            json={
                "full_name": "Updated Name",
                "phone": "0908888888",
                "is_active": True,
            },
        )

        assert response.status_code == 200
        assert response.json["user"]["full_name"] == "Updated Name"
        assert response.json["user"]["phone"] == "0908888888"

    def test_update_user_role(self, client, admin_headers, customer_user):
        """Test update user role"""
        response = client.put(
            f"/api/v1/admin/users/{customer_user.id}",
            headers=admin_headers,
            json={"role": "seller"},
        )

        assert response.status_code == 200
        assert response.json["user"]["role"] == "seller"

    def test_update_user_not_found(self, client, admin_headers):
        """Test update non-existent user"""
        response = client.put(
            "/api/v1/admin/users/invalid-id",
            headers=admin_headers,
            json={"full_name": "Test"},
        )

        assert response.status_code == 404

    def test_deactivate_user_success(self, client, admin_headers, customer_user):
        """Test deactivate user"""
        response = client.put(
            f"/api/v1/admin/users/{customer_user.id}/deactivate",
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json["user"]["is_active"] is False

    def test_deactivate_own_account(self, client, admin_headers, admin_user):
        """Test cannot deactivate own account"""
        response = client.put(
            f"/api/v1/admin/users/{admin_user.id}/deactivate",
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "Cannot deactivate your own account" in response.json["error"]

    def test_activate_user_success(self, client, admin_headers, customer_user):
        """Test activate user"""
        # First deactivate
        customer_user.is_active = False
        db.session.commit()

        # Then activate
        response = client.put(
            f"/api/v1/admin/users/{customer_user.id}/activate",
            headers=admin_headers,
        )

        assert response.status_code == 200
        assert response.json["user"]["is_active"] is True

    def test_delete_user_success(self, client, admin_headers, customer_user):
        """Test delete user (soft delete)"""
        response = client.delete(
            f"/api/v1/admin/users/{customer_user.id}",
            headers=admin_headers,
        )

        assert response.status_code == 200

        # Verify user is soft deleted
        from app.models.user import User

        deleted_user = User.query.get(customer_user.id)
        assert deleted_user.is_deleted is True

    def test_delete_own_account(self, client, admin_headers, admin_user):
        """Test cannot delete own account"""
        response = client.delete(
            f"/api/v1/admin/users/{admin_user.id}",
            headers=admin_headers,
        )

        assert response.status_code == 400
        assert "Cannot delete your own account" in response.json["error"]

    def test_reset_user_password_success(self, client, admin_headers, customer_user):
        """Test reset user password"""
        response = client.post(
            f"/api/v1/admin/users/{customer_user.id}/reset-password",
            headers=admin_headers,
            json={"new_password": "newpassword123"},
        )

        assert response.status_code == 200

        # Verify password was changed
        db.session.refresh(customer_user)
        assert customer_user.check_password("newpassword123")

    def test_reset_password_invalid_length(self, client, admin_headers, customer_user):
        """Test reset password with invalid length"""
        response = client.post(
            f"/api/v1/admin/users/{customer_user.id}/reset-password",
            headers=admin_headers,
            json={"new_password": "12345"},  # Less than 6 characters
        )

        assert response.status_code == 400

    def test_reset_password_missing_field(self, client, admin_headers, customer_user):
        """Test reset password without new_password field"""
        response = client.post(
            f"/api/v1/admin/users/{customer_user.id}/reset-password",
            headers=admin_headers,
            json={},
        )

        assert response.status_code == 400
