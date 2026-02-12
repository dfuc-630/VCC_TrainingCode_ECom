from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.wallet_service import WalletService
from app.utils.decorators import role_required
from app.enums import UserRole
from app.utils.validators import validate_schema, validate_pagination
from app.schemas import WalletDepositSchema

wallet_bp = Blueprint("wallet", __name__)

@wallet_bp.route("/", methods=["GET"])
@jwt_required()
@role_required(UserRole.CUSTOMER)
def get_wallet(current_user):
    try:
        wallet = WalletService.get_wallet_by_user_id(current_user.id)
        return jsonify({"wallet": wallet.to_dict()}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@wallet_bp.route("/deposit", methods=["POST"])
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


@wallet_bp.route("/transactions", methods=["GET"])
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