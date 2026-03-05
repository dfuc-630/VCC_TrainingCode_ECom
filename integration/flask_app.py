"""
Flask application factory with DDD integration
Sets up the Flask app with all DDD domains and routes
"""

from flask import Flask
from app.extensions import db
from integration.container import ServiceContainer
from ddd.user_management.infrastructure.api.user_routes import create_user_routes
from ddd.order_management.infrastructure.api.order_routes import create_order_routes
from ddd.payment.infrastructure.api.wallet_routes import create_wallet_routes
from ddd.product_catalog.infrastructure.api.product_routes import create_product_routes


def create_ddd_app(config=None):
    """
    Create Flask application with DDD architecture
    
    Args:
        config: Configuration object or dict
        
    Returns:
        Flask application instance
    """
    app = Flask(__name__)
    
    # Configure app
    if config:
        if isinstance(config, dict):
            app.config.update(config)
        else:
            app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    
    # Create DI container
    container = ServiceContainer(
        db_session=db.session,
        use_kafka=app.config.get('USE_KAFKA', False),
    )
    app.container = container
    
    # Register blueprints
    app.register_blueprint(create_user_routes(container), url_prefix='/api/v1')
    app.register_blueprint(create_order_routes(container), url_prefix='/api/v1')
    app.register_blueprint(create_wallet_routes(container), url_prefix='/api/v1')
    app.register_blueprint(create_product_routes(container), url_prefix='/api/v1')
    
    # Create tables
    with app.app_context():
        db.create_all()
    
    return app


def create_testing_app():
    """
    Create Flask app for testing (with in-memory SQLite)
    
    Returns:
        Flask application instance configured for testing
    """
    config = {
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'TESTING': True,
        'USE_KAFKA': False,  # Use in-memory dispatcher for tests
    }
    
    return create_ddd_app(config)
