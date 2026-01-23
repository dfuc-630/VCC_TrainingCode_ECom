from app.routes.auth import auth_bp
from app.routes.customer import customer_bp
from app.routes.seller import seller_bp
from app.routes.admin import admin_bp


def register_blueprints(app):
    """Register all blueprints"""
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(customer_bp, url_prefix='/api/customer')
    app.register_blueprint(seller_bp, url_prefix='/api/seller')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')