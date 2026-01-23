from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.schemas import ProductCreateSchema, ProductUpdateSchema
from app.utils.validators import validate_schema, validate_pagination
from app.utils.decorators import role_required
from app.enums import UserRole, OrderStatus
from sqlalchemy import func
from app.models.order import Order
from app.extensions import db

seller_bp = Blueprint('seller', __name__)


# Product endpoints
@seller_bp.route('/products', methods=['GET'])
@jwt_required()
@role_required(UserRole.SELLER)
def get_products(current_user):
    """Get seller's products"""
    page, per_page = validate_pagination()
    pagination = ProductService.search_products(
        seller_id=current_user.id,
        is_active=None,
        page=page,
        per_page=per_page
    )
    
    return jsonify({
        'products': [p.to_dict() for p in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    }), 200


@seller_bp.route('/products', methods=['POST'])
@jwt_required()
@role_required(UserRole.SELLER)
@validate_schema(ProductCreateSchema)
def create_product(current_user):
    """Create new product"""
    try:
        data = request.validated_data
        product = ProductService.create_product(
            seller_id=current_user.id,
            **data
        )
        
        return jsonify({
            'message': 'Product created successfully',
            'product': product.to_dict()
        }), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


@seller_bp.route('/products/<product_id>', methods=['GET'])
@jwt_required()
@role_required(UserRole.SELLER)
def get_product(product_id, current_user):
    """Get product detail"""
    try:
        product = ProductService.get_product_by_id(product_id)
        if product.seller_id != current_user.id:
            raise ValueError('Product not found')
        return jsonify({'product': product.to_dict()}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@seller_bp.route('/products/<product_id>', methods=['PUT'])
@jwt_required()
@role_required(UserRole.SELLER)
@validate_schema(ProductUpdateSchema)
def update_product(product_id, current_user):
    """Update product"""
    try:
        data = request.validated_data
        product = ProductService.update_product(
            product_id,
            current_user.id,
            **data
        )
        
        return jsonify({
            'message': 'Product updated successfully',
            'product': product.to_dict()
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@seller_bp.route('/products/<product_id>', methods=['DELETE'])
@jwt_required()
@role_required(UserRole.SELLER)
def delete_product(product_id, current_user):
    """Delete product (soft delete)"""
    try:
        ProductService.delete_product(product_id, current_user.id)
        return jsonify({'message': 'Product deleted successfully'}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


# Order endpoints
@seller_bp.route('/orders', methods=['GET'])
@jwt_required()
@role_required(UserRole.SELLER)
def get_orders(current_user):
    """Get seller's orders"""
    status = request.args.get('status')
    page, per_page = validate_pagination()
    
    pagination = OrderService.get_orders(
        user_id=current_user.id,
        role=UserRole.SELLER,
        status=status,
        page=page,
        per_page=per_page
    )
    
    return jsonify({
        'orders': [o.to_dict() for o in pagination.items],
        'total': pagination.total,
        'page': page,
        'pages': pagination.pages
    }), 200


@seller_bp.route('/orders/<order_id>', methods=['GET'])
@jwt_required()
@role_required(UserRole.SELLER)
def get_order(order_id, current_user):
    """Get order detail"""
    try:
        order = OrderService.get_order_by_id(order_id, current_user.id, UserRole.SELLER)
        return jsonify({'order': order.to_dict(include_items=True)}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 404


@seller_bp.route('/orders/<order_id>/status', methods=['PUT'])
@jwt_required()
@role_required(UserRole.SELLER)
def update_order_status(order_id, current_user):
    """Update order status"""
    try:
        data = request.get_json()
        if 'status' not in data:
            return jsonify({'error': 'Status is required'}), 400
        
        order = OrderService.update_order_status(
            order_id,
            current_user.id,
            data['status']
        )
        
        return jsonify({
            'message': 'Order status updated successfully',
            'order': order.to_dict()
        }), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400


# Revenue endpoints
@seller_bp.route('/revenue', methods=['GET'])
@jwt_required()
@role_required(UserRole.SELLER)
def get_revenue(current_user):
    """Get seller revenue statistics"""
    # Total revenue (completed orders)
    total_revenue = db.session.query(func.sum(Order.total_amount))\
        .filter(
            Order.seller_id == current_user.id,
            Order.status == OrderStatus.COMPLETED
        ).scalar() or 0
    
    # Order statistics
    total_orders = Order.query.filter_by(seller_id=current_user.id).count()
    completed_orders = Order.query.filter_by(
        seller_id=current_user.id,
        status=OrderStatus.COMPLETED
    ).count()
    pending_orders = Order.query.filter_by(
        seller_id=current_user.id,
        status=OrderStatus.PENDING
    ).count()
    shipping_orders = Order.query.filter_by(
        seller_id=current_user.id,
        status=OrderStatus.SHIPPING
    ).count()
    
    return jsonify({
        'total_revenue': float(total_revenue),
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'pending_orders': pending_orders,
        'shipping_orders': shipping_orders
    }), 200