from flask import Blueprint
from .user_routes import user_admin_bp
from .product_routes import product_admin_bp
from .order_routes import order_admin_bp
from .dashboard_routes import dashboard_admin_bp

# Blueprint tổng của Admin
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# Đăng ký các module con với tiền tố tương ứng
admin_bp.register_blueprint(user_admin_bp, url_prefix="/users")
admin_bp.register_blueprint(product_admin_bp, url_prefix="/products")
admin_bp.register_blueprint(order_admin_bp, url_prefix="/orders")
admin_bp.register_blueprint(dashboard_admin_bp, url_prefix="/dashboard")