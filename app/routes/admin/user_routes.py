from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from app.models.user import User
from app.utils.decorators import role_required
from app.enums import UserRole
from app.utils.validators import validate_pagination
from app.extensions import db

user_admin_bp = Blueprint("users", __name__)

@user_admin_bp.route('/', methods=['GET'])
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


@user_admin_bp.route('/<user_id>', methods=['GET'])
@jwt_required()
@role_required(UserRole.ADMIN)
def get_user(user_id, current_user):
    """Get user detail"""
    user = User.query.get(user_id)
    if not user or user.is_deleted:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


@user_admin_bp.route('/<user_id>', methods=['PUT'])
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


@user_admin_bp.route('/<user_id>/deactivate', methods=['PUT'])
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


@user_admin_bp.route('/<user_id>/activate', methods=['PUT'])
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


@user_admin_bp.route('/<user_id>', methods=['DELETE'])
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


@user_admin_bp.route('/<user_id>/reset-password', methods=['POST'])
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

