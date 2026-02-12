from flask import Blueprint
from .wallet_routes import wallet_bp
from .product_routes import product_bp
from .order_routes import order_bp

customer_bp = Blueprint("customer", __name__, url_prefix="/customer")

# Đăng ký các blueprint con
customer_bp.register_blueprint(wallet_bp, url_prefix="/wallet")
customer_bp.register_blueprint(product_bp, url_prefix="/products")
customer_bp.register_blueprint(order_bp, url_prefix="/orders")