from flask import Blueprint, request, jsonify
from app.models.user import User
from app.extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash
from app.schemas import UserSchema

user_schema = UserSchema()
users_schema = UserSchema(many=True)
user_bp = Blueprint("user", __name__, url_prefix="/users")


@user_bp.route("/profile", methods=["GET"])
@jwt_required()
def profile():
    user_id = get_jwt_identity()

    user = User.query.get(user_id)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({
        "msg": "success",
        "data": user_schema.dump(user)
    }), 200


@user_bp.route("/")
@jwt_required()
def list_users():
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int)
    email = request.args.get("email")

    query = User.query

    if email:
        query = query.filter(User.email.like(f"%{email}%"))

    pagination = query.paginate(

        page=page,
        per_page=limit,
        error_out=False
    )
    users = pagination.items
    return jsonify({
        "msg": "success",
        "page": page,
        "limit": limit,
        "total": pagination.total,
        "pages": pagination.pages,
        "data": users_schema.dump(users)
    }), 200


@user_bp.route("/<int:id>")
@jwt_required()
def detail(id):
    user = User.query.get(id)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({
        "msg": "success",
        "data": user_schema.dump(user)  
    }), 200


@user_bp.route("/", methods=["POST"])
def create():
    json_data = request.get_json()

    if not json_data:
        return jsonify({"msg": "Missing JSON body"}), 400

    try:
        data = user_schema.load(json_data)
    except Exception as err:
        return jsonify(err.messages), 400

    existed = User.query.filter_by(email=data["email"]).first()

    if existed:
        return jsonify({"msg": "Email already exists"}), 409

    hashed_password = generate_password_hash(data["password"])

    user = User(
        email=data["email"],
        password=hashed_password,
        description=data.get("description")
    )

    db.session.add(user)
    db.session.commit()

    return jsonify({
        "msg": "Create User Successfully!",
        "data": user_schema.dump(user)
    }), 201