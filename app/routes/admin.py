from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.services.product_service import ProductService
from app.utils.validators import validate_pagination
from app.utils.decorators import role_required
from app.enums import UserRole, OrderStatus
from sqlalchemy import func
from app.extensions import db

admin_bp = Blueprint("admin", __name__)



# Product management
@admin_bp.route("/products", methods=["GET"])
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


@admin_bp.route("/products/<product_id>", methods=["GET"])
@jwt_required()
@role_required(UserRole.ADMIN)
def get_product(product_id, current_user):
    """Get product detail"""
    try:
        product = ProductService.get_product_by_id(product_id)
        return jsonify({"product": product.to_dict()}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


# Order management
@admin_bp.route("/orders", methods=["GET"])
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


@admin_bp.route("/orders/<order_id>", methods=["GET"])
@jwt_required()
@role_required(UserRole.ADMIN)
def get_order(order_id, current_user):
    """Get order detail"""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    return jsonify({"order": order.to_dict(include_items=True)}), 200


# Dashboard
@admin_bp.route("/dashboard", methods=["GET"])
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

# User management
@admin_bp.route('/users', methods=['GET'])
@jwt_required()
@role_required(UserRole.ADMIN)
def get_users(current_user):
    """Get all users"""
    role = request.args.get('role')
    page, per_page = validate_pagination()
    
    query = User.query.filter_by(deleted_at=None)
    
    if role:
        query = query.filter_by(role=role)
    
    pagination = query.order_by(User.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'users': [u.to_dict() for u in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    }), 200


@admin_bp.route('/users/<user_id>', methods=['GET'])
@jwt_required()
@role_required(UserRole.ADMIN)
def get_user(user_id, current_user):
    """Get user detail"""
    user = User.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


@admin_bp.route('/users/<user_id>', methods=['PUT'])
@jwt_required()
@role_required(UserRole.ADMIN)
def update_user(user_id, current_user):
    """Update user information"""
    user = User.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    # Update allowed fields
    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'phone' in data:
        user.phone = data['phone']
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'role' in data and data['role'] in ['customer', 'seller', 'admin']:
        user.role = data['role']
    
    db.session.commit()
    
    return jsonify({
        'message': 'User updated successfully',
        'user': user.to_dict()
    }), 200


@admin_bp.route('/users/<user_id>/deactivate', methods=['PUT'])
@jwt_required()
@role_required(UserRole.ADMIN)
def deactivate_user(user_id, current_user):
    """Deactivate user account"""
    user = User.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'error': 'User not found'}), 404
    
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot deactivate your own account'}), 400
    
    user.is_active = False
    db.session.commit()
    
    return jsonify({
        'message': 'User deactivated successfully',
        'user': user.to_dict()
    }), 200


@admin_bp.route('/users/<user_id>/activate', methods=['PUT'])
@jwt_required()
@role_required(UserRole.ADMIN)
def activate_user(user_id, current_user):
    """Activate user account"""
    user = User.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'error': 'User not found'}), 404
    
    user.is_active = True
    db.session.commit()
    
    return jsonify({
        'message': 'User activated successfully',
        'user': user.to_dict()
    }), 200


@admin_bp.route('/users/<user_id>', methods=['DELETE'])
@jwt_required()
@role_required(UserRole.ADMIN)
def delete_user(user_id, current_user):
    """Delete user (soft delete)"""
    user = User.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'error': 'User not found'}), 404
    
    if user.id == current_user.id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    user.soft_delete()
    
    return jsonify({'message': 'User deleted successfully'}), 200


@admin_bp.route('/users/<user_id>/reset-password', methods=['POST'])
@jwt_required()
@role_required(UserRole.ADMIN)
def reset_user_password(user_id, current_user):
    """Reset user password"""
    user = User.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    if 'new_password' not in data:
        return jsonify({'error': 'New password is required'}), 400
    
    if len(data['new_password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    user.set_password(data['new_password'])
    db.session.commit()
    
    return jsonify({'message': 'Password reset successfully'}), 200
