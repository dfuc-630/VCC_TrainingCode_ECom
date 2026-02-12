from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.user import User
from app.utils.decorators import role_required
from app.enums import UserRole
from app.utils.validators import validate_pagination
from app.extensions import db
from app.models.order import Order

order_admin_bp = Blueprint("orders", __name__)

@order_admin_bp.route("/", methods=["GET"])
@jwt_required()
@role_required(UserRole.ADMIN)
def get_orders(current_user):
    """Get all orders"""
    status = request.args.get("status")
    customer_id = request.args.get("customer_id")
    seller_id = request.args.get("seller_id")
    page, per_page = validate_pagination()

    query = Order.query

    if status:
        query = query.filter_by(status=status)
    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    if seller_id:
        query = query.filter_by(seller_id=seller_id)

    pagination = query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return (
        jsonify(
            {
                "orders": [o.to_dict() for o in pagination.items],
                "total": pagination.total,
                "page": page,
                "pages": pagination.pages,
            }
        ),
        200,
    )


@order_admin_bp.route("/<order_id>", methods=["GET"])
@jwt_required()
@role_required(UserRole.ADMIN)
def get_order(order_id, current_user):
    """Get order detail"""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    return jsonify({"order": order.to_dict(include_items=True)}), 200