from flask import jsonify
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from werkzeug.exceptions import HTTPException
from flask_jwt_extended.exceptions import JWTDecodeError, NoAuthorizationError, InvalidHeaderError


def register_error_handlers(app):
    """Register error handlers"""

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"error": "Bad request"}), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal error: {error}")
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(error):
        return (
            jsonify({"error": "Database integrity error", "details": str(error.orig)}),
            409,
        )

    @app.errorhandler(SQLAlchemyError)
    def handle_sqlalchemy_error(error):
        app.logger.error(f"Database error: {error}")
        return jsonify({"error": "Database error"}), 500

    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({"error": error.description}), error.code
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({"error": "Forbidden"}), 403
    
    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({"error": "Unauthorized"}), 401
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        return jsonify({"error": "Unprocessable entity"}), 422

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"Unhandled exception: {error}")
        return jsonify({"error": "An unexpected error occurred"}), 500
    
    # JWT Error Handlers
    @app.errorhandler(NoAuthorizationError)
    def handle_no_authorization(error):
        return jsonify({"error": "Missing authorization header"}), 401
    
    @app.errorhandler(JWTDecodeError)
    def handle_jwt_decode_error(error):
        return jsonify({"error": "Invalid token"}), 422
    
    @app.errorhandler(InvalidHeaderError)
    def handle_invalid_header(error):
        return jsonify({"error": "Invalid authorization header"}), 422