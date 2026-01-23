from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User


def role_required(*roles):
    """Decorator to check if user has required role"""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user_id = get_jwt_identity()
            user = User.query.get(user_id)
            
            if not user or not user.is_active or user.is_deleted:
                return jsonify({'error': 'User not found or inactive'}), 403
            
            if user.role not in roles:
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            # Pass user to route handler
            kwargs['current_user'] = user
            return fn(*args, **kwargs)
        return wrapper
    return decorator