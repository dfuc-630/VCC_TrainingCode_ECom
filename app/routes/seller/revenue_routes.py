from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required
from app.utils.decorators import role_required
from app.enums import UserRole, OrderStatus
from app.models.order import Order
from app.extensions import db
from sqlalchemy import func

revenue_seller_bp = Blueprint("revenue", __name__)

@revenue_seller_bp.route("/", methods=["GET"])
@jwt_required()
@role_required(UserRole.SELLER)
def get_revenue(current_user):
    # Total revenue (completed orders)
    total_revenue = (
        db.session.query(func.sum(Order.total_amount))
        .filter(
            Order.seller_id == current_user.id, Order.status == OrderStatus.COMPLETED
        )
        .scalar()
        or 0
    )

    # Order statistics
    total_orders = Order.query.filter_by(seller_id=current_user.id).count()
    completed_orders = Order.query.filter_by(
        seller_id=current_user.id, status=OrderStatus.COMPLETED
    ).count()
    pending_orders = Order.query.filter_by(
        seller_id=current_user.id, status=OrderStatus.PENDING
    ).count()
    shipping_orders = Order.query.filter_by(
        seller_id=current_user.id, status=OrderStatus.SHIPPING
    ).count()

    return (
        jsonify(
            {
                "total_revenue": float(total_revenue),
                "total_orders": total_orders,
                "completed_orders": completed_orders,
                "pending_orders": pending_orders,
                "shipping_orders": shipping_orders,
            }
        ),
        200,
    )
