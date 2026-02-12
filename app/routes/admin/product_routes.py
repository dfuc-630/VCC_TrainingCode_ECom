from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.user import User
from app.utils.decorators import role_required
from app.enums import UserRole
from app.utils.validators import validate_pagination
from app.extensions import db
from app.services.product_service import ProductService

product_admin_bp = Blueprint("products", __name__)

@product_admin_bp.route("/", methods=["GET"])
@jwt_required()
@role_required(UserRole.ADMIN)
def get_products(current_user):
    """Get all products"""
    search = request.args.get("search")
    seller_id = request.args.get("seller_id")
    is_active = request.args.get("is_active", type=bool)
    page, per_page = validate_pagination()

    pagination = ProductService.search_products(
        search=search,
        seller_id=seller_id,
        is_active=is_active,
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


@product_admin_bp.route("/<product_id>", methods=["GET"])
@jwt_required()
@role_required(UserRole.ADMIN)
def get_product(product_id, current_user):
    """Get product detail"""
    try:
        product = ProductService.get_product_by_id(product_id)
        return jsonify({"product": product.to_dict()}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
