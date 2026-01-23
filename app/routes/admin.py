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

admin_bp = Blueprint('admin', __name__)


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


# Product management
@admin_bp.route('/products', methods=['GET'])
@jwt_required()
@role_required(UserRole.ADMIN)
def get_products(current_user):
    """Get all products"""
    search = request.args.get('search')
    seller_id = request.args.get('seller_id')
    is_active = request.args.get('is_active', type=bool)
    page, per_page = validate_pagination()
    
    pagination = ProductService.search_products(
        search=search,
        seller_id=seller_id,
        is_active=is_active,
        page=page,
        per_page=per_page
    )
    
    return jsonify({
        'products': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    }), 200


@admin_bp.route('/products/<product_id>', methods=['GET'])
@jwt_required()
@role_required(UserRole.ADMIN)
def get_product(product_id, current_user):
    """Get product detail"""
    try:
        product = ProductService.get_product_by_id(product_id)
        return jsonify({'product': product.to_dict()}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


# Order management
@admin_bp.route('/orders', methods=['GET'])
@jwt_required()
@role_required(UserRole.ADMIN)
def get_orders(current_user):
    """Get all orders"""
    status = request.args.get('status')
    customer_id = request.args.get('customer_id')
    seller_id = request.args.get('seller_id')
    page, per_page = validate_pagination()
    
    query = Order.query
    
    if status:
        query = query.filter_by(status=status)
    if customer_id:
        query = query.filter_by(customer_id=customer_id)
    if seller_id:
        query = query.filter_by(seller_id=seller_id)
    
    pagination = query.order_by(Order.created_at.desc())\
        .paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'orders': [o.to_dict() for o in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    }), 200


@admin_bp.route('/orders/<order_id>', methods=['GET'])
@jwt_required()
@role_required(UserRole.ADMIN)
def get_order(order_id, current_user):
    """Get order detail"""
    order = Order.query.get(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    
    return jsonify({'order': order.to_dict(include_items=True)}), 200


# Dashboard
@admin_bp.route('/dashboard', methods=['GET'])
@jwt_required()
@role_required(UserRole.ADMIN)
def get_dashboard(current_user):
    """Get admin dashboard statistics"""
    # User statistics
    total_users = User.query.filter_by(deleted_at=None).count()
    total_customers = User.query.filter_by(role=UserRole.CUSTOMER, deleted_at=None).count()
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
    total_revenue = db.session.query(func.sum(Order.total_amount))\
        .filter(Order.status == OrderStatus.COMPLETED).scalar() or 0
    
    return jsonify({
        'users': {
            'total': total_users,
            'customers': total_customers,
            'sellers': total_sellers,
            'active': active_users
        },
        'products': {
            'total': total_products,
            'active': active_products,
            'out_of_stock': out_of_stock
        },
        'orders': {
            'total': total_orders,
            'pending': pending_orders,
            'completed': completed_orders,
            'cancelled': cancelled_orders
        },
        'revenue': {
            'total': float(total_revenue)
        }
    }), 200
