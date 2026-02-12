from flask import Blueprint
from .product_routes import product_seller_bp
from .order_routes import order_seller_bp
from .revenue_routes import revenue_seller_bp

# Khởi tạo Blueprint cha cho Seller
seller_bp = Blueprint("seller", __name__, url_prefix="/seller")

# Đăng ký các Blueprint con
seller_bp.register_blueprint(product_seller_bp, url_prefix="/products")
seller_bp.register_blueprint(order_seller_bp, url_prefix="/orders")
seller_bp.register_blueprint(revenue_seller_bp, url_prefix="/revenue")