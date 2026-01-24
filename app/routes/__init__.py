from app.routes.auth import auth_bp
from app.routes.customer import customer_bp
from app.routes.seller import seller_bp
from app.routes.admin import admin_bp

# from app.routes.user import user_bp


def register_blueprints(app):
    """Register all blueprints"""
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(customer_bp, url_prefix="/api/v1/customer")
    app.register_blueprint(seller_bp, url_prefix="/api/v1/seller")
    app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
    # app.register_blueprint(user_bp, url_prefix='/api/v1/user')
