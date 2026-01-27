from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.wallet_service import WalletService
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.schemas import WalletDepositSchema, OrderCreateSchema
from app.utils.validators import validate_schema, validate_pagination
from app.utils.decorators import role_required
from app.enums import UserRole

customer_bp = Blueprint("customer", __name__)


# Wallet endpoints
@customer_bp.route("/wallet", methods=["GET"])
@jwt_required()
@role_required(UserRole.CUSTOMER)
def get_wallet(current_user):
    try:
        wallet = WalletService.get_wallet_by_user_id(current_user.id)
        return jsonify({"wallet": wallet.to_dict()}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@customer_bp.route("/wallet/deposit", methods=["POST"])
@jwt_required()
@role_required(UserRole.CUSTOMER)
@validate_schema(WalletDepositSchema)
def deposit(current_user):
    """Deposit money to wallet"""
    try:
        data = request.validated_data
        wallet = WalletService.get_wallet_by_user_id(current_user.id)
        wallet, transaction = WalletService.deposit(
            wallet.id, data["amount"], data.get("description")
        ) # using Pessimistic Locking instead of Optimistic

        return (
            jsonify(
                {
                    "message": "Deposit successful",
                    "wallet": wallet.to_dict(),
                    "transaction": transaction.to_dict(),
                }
            ),
            200,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@customer_bp.route("/wallet/transactions", methods=["GET"])
@jwt_required()
@role_required(UserRole.CUSTOMER)
def get_transactions(current_user):
    """Get wallet transactions"""
    try:
        wallet = WalletService.get_wallet_by_user_id(current_user.id)
        page, per_page = validate_pagination()
        pagination = WalletService.get_transactions(wallet.id, page, per_page)

        return (
            jsonify(
                {
                    "transactions": [t.to_dict() for t in pagination.items],
                    "total": pagination.total,
                    "page": page,
                    "pages": pagination.pages,
                }
            ),
            200,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 404

# --maybe can add search transactions api

# Product endpoints
@customer_bp.route("/products", methods=["GET"])
@jwt_required()
def search_products():
    """Search products"""
    search = request.args.get("search", "")
    category_id = request.args.get("category_id")
    seller_id = request.args.get("seller_id") # add seller_id
    page, per_page = validate_pagination()

    pagination = ProductService.search_products(
        search=search,
        category_id=category_id,
        seller_id=seller_id,
        is_active=True,
        page=page,
        per_page=per_page,
    )

    return (
        jsonify(
            {
                "products": [p.to_dict() for p in pagination.items],
                "total": pagination.total,
                "page": page,
                "pages": pagination.pages,
            }
        ),
        200,
    )


@customer_bp.route("/products/<product_id>", methods=["GET"])
@jwt_required()
def get_product(product_id):
    """Get product detail"""
    try:
        product = ProductService.get_product_by_id(product_id) # did raise same error in service
        if not product.is_active:
            raise ValueError("Product not found")
        return jsonify({"product": product.to_dict()}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# Order endpoints
@customer_bp.route("/orders", methods=["POST"])
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

        return (
            jsonify(
                {
                    "message": "Order created successfully",
                    "order": order.to_dict(include_items=True),
                }
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@customer_bp.route("/orders", methods=["GET"])
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


@customer_bp.route("/orders/<order_id>", methods=["GET"])
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


@customer_bp.route("/orders/<order_id>/cancel", methods=["PUT"])
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
