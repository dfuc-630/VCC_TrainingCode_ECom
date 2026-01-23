from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from app.models.user import User
from app.extensions import db

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["POST"])
def register():

    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return {"msg": "Missing data"}, 400

    if User.query.filter_by(email=email).first():
        return {"msg": "Email exists"}, 409

    hashed = generate_password_hash(password)

    user = User(email=email, password=hashed)

    db.session.add(user)
    db.session.commit()

    return {"msg": "Register success"}, 201


@auth_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    user = User.query.filter_by(email=data.get("email")).first()

    if not user:
        return {"msg": "Invalid"}, 401

    if not check_password_hash(user.password, data.get("password")):
        return {"msg": "Invalid"}, 401

    token = create_access_token(identity=user.id)

    return jsonify(access_token=token)
