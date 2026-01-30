import pytest
from flask import Flask
from app.utils.error_handlers import register_error_handlers
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.exceptions import HTTPException


class TestErrorHandlers:
    """Test error handlers"""

    def test_400_error_handler(self, app):
        """Test 400 error handler"""
        client = app.test_client()

        @app.route("/test-400")
        def test_400():
            from werkzeug.exceptions import BadRequest
            raise BadRequest()

        response = client.get("/test-400")
        assert response.status_code == 400

    def test_404_error_handler(self, app):
        """Test 404 error handler"""
        client = app.test_client()

        response = client.get("/nonexistent-route")
        assert response.status_code == 404
        assert "error" in response.json

    def test_500_error_handler(self, app):
        """Test 500 error handler"""
        client = app.test_client()

        @app.route("/test-500")
        def test_500():
            raise Exception("Test error")

        response = client.get("/test-500")
        assert response.status_code == 500
        assert "error" in response.json

    def test_integrity_error_handler(self, app):
        """Test IntegrityError handler"""
        client = app.test_client()

        @app.route("/test-integrity")
        def test_integrity():
            raise IntegrityError("test", "test", "test")

        response = client.get("/test-integrity")
        assert response.status_code == 409
