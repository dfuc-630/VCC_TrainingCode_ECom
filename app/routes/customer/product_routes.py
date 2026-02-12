from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.wallet_service import WalletService
from app.utils.decorators import role_required
from app.enums import UserRole
from app.utils.validators import validate_schema, validate_pagination
from app.schemas import WalletDepositSchema
from app.services.product_service import ProductService

product_bp = Blueprint("products", __name__)


@product_bp.route("/", methods=["GET"])
@jwt_required()
def search_products():
    """Search products"""
    search = request.args.get("search", "")
    category_id = request.args.get("category_id")
    seller_id = request.args.get("seller_id")
    
    page, per_page = validate_pagination()

    pagination = ProductService.search_products(search=search, category_id=category_id, seller_id=seller_id, is_active=True, page=page, per_page=per_page,)

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


@product_bp.route("/<product_id>", methods=["GET"])
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