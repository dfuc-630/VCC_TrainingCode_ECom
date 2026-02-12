from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.wallet_service import WalletService
from app.utils.decorators import role_required
from app.enums import UserRole
from app.utils.validators import validate_schema, validate_pagination
from app.schemas import OrderCreateSchema, WalletDepositSchema
from app.services.product_service import ProductService
from app.services.order_service import OrderService

order_bp = Blueprint("orders", __name__)
@order_bp.route("/", methods=["POST"])
@jwt_required()
@role_required(UserRole.CUSTOMER)
@validate_schema(OrderCreateSchema)
def create_order(current_user): #checked
    """Create new order"""
    try:
        data = request.validated_data
        order = OrderService.create_order(
            customer_id=current_user.id,
            items_data=data["items"],
            shipping_address=data["shipping_address"],
            shipping_phone=data["shipping_phone"],
        )
        # order_item_producer_send(order) # send kafka order_item_events topic
        return (
            jsonify(
                {
                    "message": "Order created successfully, waiting for confirmed",
                    "order": order.to_dict(include_items=True),
                }
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@order_bp.route("/", methods=["GET"])
@jwt_required()
@role_required(UserRole.CUSTOMER)
def get_orders(current_user):
    """Get customer orders"""
    status = request.args.get("status")
    page, per_page = validate_pagination()

    pagination = OrderService.get_orders(
        user_id=current_user.id,
        role=UserRole.CUSTOMER,
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

@order_bp.route("/<order_id>", methods=["GET"])
@jwt_required()
@role_required(UserRole.CUSTOMER)
def get_order(order_id, current_user):
    """Get order detail"""
    try:
        order = OrderService.get_order_by_id(
            order_id, current_user.id, UserRole.CUSTOMER
        )
        return jsonify({"order": order.to_dict(include_items=True)}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@order_bp.route("/<order_id>/cancel", methods=["PUT"])
@jwt_required()
@role_required(UserRole.CUSTOMER)
def cancel_order(order_id, current_user):
    """Cancel order"""
    try:
        order = OrderService.cancel_order(order_id, current_user.id)
        return (
            jsonify(
                {"message": "Order cancelled successfully", "order": order.to_dict()}
            ),
            200,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400