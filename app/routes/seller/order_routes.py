from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.order_service import OrderService
from app.utils.decorators import role_required
from app.utils.validators import validate_pagination
from app.enums import UserRole

order_seller_bp = Blueprint("orders", __name__)

@order_seller_bp.route("/", methods=["GET"])
@jwt_required()
@role_required(UserRole.SELLER)
def get_orders(current_user):
    """Get seller's orders"""
    status = request.args.get("status")
    page, per_page = validate_pagination()

    pagination = OrderService.get_orders(
        user_id=current_user.id,
        role=UserRole.SELLER,
        status=status,
        page=page,
        per_page=per_page,
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


@order_seller_bp.route("/<order_id>", methods=["GET"])
@jwt_required()
@role_required(UserRole.SELLER)
def get_order(order_id, current_user):
    try:
        order = OrderService.get_order_by_id(order_id, current_user.id, UserRole.SELLER)
        return jsonify({"order": order.to_dict(include_items=True)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@order_seller_bp.route("/<order_id>/status", methods=["PUT"])
@jwt_required()
@role_required(UserRole.SELLER)
def update_order_status(order_id, current_user):
    try:
        data = request.get_json()
        if "status" not in data:
            return jsonify({"error": "Status is required"}), 400

        order = OrderService.update_order_status(
            order_id, current_user.id, data["status"]
        )

        return (
            jsonify(
                {
                    "message": "Order status updated successfully",
                    "order": order.to_dict(),
                }
            ),
            200,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400