from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.product_service import ProductService
from app.utils.decorators import role_required
from app.utils.validators import validate_schema, validate_pagination
from app.schemas import ProductCreateSchema, ProductUpdateSchema
from app.enums import UserRole

product_seller_bp = Blueprint("products", __name__)

@product_seller_bp.route("/", methods=["GET"])
@jwt_required()
@role_required(UserRole.SELLER)
def get_products(current_user):
    page, per_page = validate_pagination()
    pagination = ProductService.search_products(
        seller_id=current_user.id, is_active=None, page=page, per_page=per_page
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


@product_seller_bp.route("/", methods=["POST"])
@jwt_required()
@role_required(UserRole.SELLER)
@validate_schema(ProductCreateSchema)
def create_product(current_user):
    try:
        data = request.validated_data
        product = ProductService.create_product(seller_id=current_user.id, **data)

        return (
            jsonify(
                {
                    "message": "Product created successfully",
                    "product": product.to_dict(),
                }
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@product_seller_bp.route("/<product_id>", methods=["GET"])
@jwt_required()
@role_required(UserRole.SELLER)
def get_product(product_id, current_user):
    try:
        product = ProductService.get_product_by_id(product_id)
        if product.seller_id != current_user.id:
            raise ValueError("Product not found")
        return jsonify({"product": product.to_dict()}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@product_seller_bp.route("/<product_id>", methods=["PUT"])
@jwt_required()
@role_required(UserRole.SELLER)
@validate_schema(ProductUpdateSchema)
def update_product(product_id, current_user):
    try:
        data = request.validated_data
        product = ProductService.update_product(product_id, current_user.id, **data)

        return (
            jsonify(
                {
                    "message": "Product updated successfully",
                    "product": product.to_dict(),
                }
            ),
            200,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@product_seller_bp.route("/<product_id>", methods=["DELETE"])
@jwt_required()
@role_required(UserRole.SELLER)
def delete_product(product_id, current_user):
    try:
        ProductService.delete_product(product_id, current_user.id)
        return jsonify({"message": "Product deleted successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404