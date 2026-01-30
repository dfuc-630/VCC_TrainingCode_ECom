from flask import Flask, jsonify
from .extensions import db, migrate, jwt, ma
from .config import Config
from app.utils.error_handlers import register_error_handlers
from app.routes import register_blueprints


def create_app():

    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    ma.init_app(app)

    # from .routes.auth import auth_bp
    # from .routes.user import user_bp

    # app.register_blueprint(auth_bp)
    # app.register_blueprint(user_bp)

    register_blueprints(app)
    register_error_handlers(app)
    
    # Register JWT error handlers
    from flask_jwt_extended.exceptions import JWTDecodeError, NoAuthorizationError, InvalidHeaderError
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired"}), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"error": "Invalid token"}), 422
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"error": "Missing authorization header"}), 401

    @app.route("/health")
    def health():
        return {"status": "healthy"}, 20

    return app
