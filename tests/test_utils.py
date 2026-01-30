import pytest
from flask import Flask, request, jsonify
from app.utils.decorators import role_required
from app.utils.validators import validate_schema, validate_pagination
from app.utils.helpers import generate_order_number, slugify, allowed_file
from app.enums import UserRole
from marshmallow import Schema, fields


class TestDecorators:
    """Test decorator utilities"""

    def test_role_required_success(self, app, customer_user, customer_token):
        """Test role_required decorator with correct role"""
        with app.test_request_context(
            headers={"Authorization": f"Bearer {customer_token}"}
        ):
            from flask_jwt_extended import create_access_token

            @role_required(UserRole.CUSTOMER)
            def test_route(current_user):
                return jsonify({"success": True})

            response = test_route()
            assert response.status_code == 200

    def test_role_required_wrong_role(self, app, customer_user, customer_token):
        """Test role_required decorator with wrong role"""
        with app.test_request_context(
            headers={"Authorization": f"Bearer {customer_token}"}
        ):
            @role_required(UserRole.ADMIN)
            def test_route(current_user):
                return jsonify({"success": True})

            response = test_route()
            assert response.status_code == 403


class TestValidators:
    """Test validator utilities"""

    def test_validate_pagination_default(self, app):
        """Test pagination with default values"""
        with app.test_request_context():
            page, per_page = validate_pagination()
            assert page == 1
            assert per_page == 20

    def test_validate_pagination_custom(self, app):
        """Test pagination with custom values"""
        with app.test_request_context("/?page=2&per_page=10"):
            page, per_page = validate_pagination()
            assert page == 2
            assert per_page == 10

    def test_validate_pagination_invalid_page(self, app):
        """Test pagination with invalid page"""
        with app.test_request_context("/?page=0&per_page=10"):
            page, per_page = validate_pagination()
            assert page == 1  # Should default to 1

    def test_validate_pagination_invalid_per_page(self, app):
        """Test pagination with invalid per_page"""
        with app.test_request_context("/?page=1&per_page=200"):
            page, per_page = validate_pagination()
            assert per_page == 20  # Should default to 20

    def test_validate_schema_success(self, app):
        """Test schema validation success"""
        class TestSchema(Schema):
            name = fields.Str(required=True)

        @validate_schema(TestSchema)
        def test_route():
            return jsonify({"success": True})

        with app.test_request_context(
            "/", method="POST", json={"name": "Test"}
        ):
            response = test_route()
            assert response.status_code == 200

    def test_validate_schema_failure(self, app):
        """Test schema validation failure"""
        class TestSchema(Schema):
            name = fields.Str(required=True)

        @validate_schema(TestSchema)
        def test_route():
            return jsonify({"success": True})

        with app.test_request_context("/", method="POST", json={}):
            result = test_route()
            # validate_schema returns tuple (response, status_code) on error
            if isinstance(result, tuple):
                response, status_code = result
                assert status_code == 400
            else:
                assert result.status_code == 400


class TestHelpers:
    """Test helper utilities"""

    def test_generate_order_number(self):
        """Test order number generation"""
        order_num = generate_order_number()
        assert order_num.startswith("ORD")
        assert len(order_num) > 10

    def test_generate_order_number_unique(self):
        """Test order numbers are unique"""
        order_num1 = generate_order_number()
        order_num2 = generate_order_number()
        assert order_num1 != order_num2

    def test_slugify(self):
        """Test slug generation"""
        assert slugify("Hello World") == "hello-world"
        assert slugify("Test Product 123") == "test-product-123"
        assert slugify("Special@Chars#Here") == "special-chars-here"

    def test_allowed_file(self):
        """Test file extension check"""
        assert allowed_file("test.jpg", {"jpg", "png"}) is True
        assert allowed_file("test.JPG", {"jpg", "png"}) is True
        assert allowed_file("test.pdf", {"jpg", "png"}) is False
        assert allowed_file("test", {"jpg", "png"}) is False
