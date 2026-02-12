from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.user import User
from app.utils.decorators import role_required
from app.enums import OrderStatus, UserRole
from app.utils.validators import validate_pagination
from app.extensions import db
from app.models.order import Order
from app.models.product import Product
from sqlalchemy import func

dashboard_admin_bp = Blueprint("dashboard_admin", __name__)

@dashboard_admin_bp.route("/", methods=["GET"])
@jwt_required()
@role_required(UserRole.ADMIN)
def get_dashboard(current_user):
    """Get admin dashboard statistics"""
    # User statistics
    total_users = User.query.filter_by(deleted_at=None).count()
    total_customers = User.query.filter_by(
        role=UserRole.CUSTOMER, deleted_at=None
    ).count()
    total_sellers = User.query.filter_by(role=UserRole.SELLER, deleted_at=None).count()
    active_users = User.query.filter_by(is_active=True, deleted_at=None).count()

    # Product statistics
    total_products = Product.query.filter_by(deleted_at=None).count()
    active_products = Product.query.filter_by(is_active=True, deleted_at=None).count()
    out_of_stock = Product.query.filter_by(stock_quantity=0, deleted_at=None).count()

    # Order statistics
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status=OrderStatus.PENDING).count()
    completed_orders = Order.query.filter_by(status=OrderStatus.COMPLETED).count()
    cancelled_orders = Order.query.filter_by(status=OrderStatus.CANCELLED).count()

    # Revenue statistics
    total_revenue = (
        db.session.query(func.sum(Order.total_amount))
        .filter(Order.status == OrderStatus.COMPLETED)
        .scalar()
        or 0
    )

    return (
        jsonify(
            {
                "users": {
                    "total": total_users,
                    "customers": total_customers,
                    "sellers": total_sellers,
                    "active": active_users,
                },
                "products": {
                    "total": total_products,
                    "active": active_products,
                    "out_of_stock": out_of_stock,
                },
                "orders": {
                    "total": total_orders,
                    "pending": pending_orders,
                    "completed": completed_orders,
                    "cancelled": cancelled_orders,
                },
                "revenue": {"total": float(total_revenue)},
            }
        ),
        200,
    )