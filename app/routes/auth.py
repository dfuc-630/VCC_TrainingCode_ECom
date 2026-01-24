from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token
from app.services.auth_service import AuthService
from app.schemas import UserRegisterSchema, UserLoginSchema
from app.utils.validators import validate_schema

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["POST"])
@validate_schema(UserRegisterSchema)
def register():
    """Register new user"""
    try:
        data = request.validated_data
        user = AuthService.register_user(**data)

        return (
            jsonify(
                {"message": "User registered successfully", "user": user.to_dict()}
            ),
            201,
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@auth_bp.route("/login", methods=["POST"])
@validate_schema(UserLoginSchema)
def login():
    """User login"""
    try:
        data = request.validated_data
        result = AuthService.login_user(**data)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 401


@auth_bp.route("/refresh", methods=["POST"])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token"""
    user_id = get_jwt_identity()
    access_token = create_access_token(identity=user_id)
    return jsonify({"access_token": access_token}), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required()
def get_me():
    """Get current user info"""
    try:
        user_id = get_jwt_identity()
        user = AuthService.get_user_by_id(user_id)
        return jsonify({"user": user.to_dict()}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
