from functools import wraps
from flask import request, jsonify
from marshmallow import ValidationError


def validate_schema(schema_class):
    """Decorator to validate request data against schema"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            schema = schema_class()
            try:
                validated_data = schema.load(request.get_json())
                request.validated_data = validated_data
                return f(*args, **kwargs)
            except ValidationError as err:
                return jsonify({'error': 'Validation error', 'messages': err.messages}), 400
        return decorated_function
    return decorator


def validate_pagination():
    """Validate pagination parameters"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20
    
    return page, per_page