from app.models.user import User
from app.models.wallet import Wallet
from app.extensions import db
from flask_jwt_extended import create_access_token, create_refresh_token


class AuthService:
    """Single Responsibility Principle"""

    @staticmethod
    def register_user(email: str, username: str, password: str, role: str, **kwargs) -> User:
        # Check if user exists
        if User.query.filter_by(email=email).first():
            raise ValueError("Email already exists")

        if User.query.filter_by(username=username).first():
            raise ValueError("Username already exists")

        # Create user
        user = User(
            email=email,
            username=username,
            role=role,
            full_name=kwargs.get("full_name"),
            phone=kwargs.get("phone"),
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        # print("user.id: ", user.id)

        # Create wallet for customer
        # if role == "customer":
        wallet = Wallet(user_id=user.id)
        db.session.add(wallet)

        db.session.commit()
        return user

    @staticmethod
    def login_user(username: str, password: str) -> dict:
        """Authenticate user and generate tokens"""
        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            raise ValueError("Invalid credentials")

        if not user.is_active or user.is_deleted:
            raise ValueError("Account is deactivated")

        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user": user.to_dict(),
        }

    @staticmethod
    def get_user_by_id(user_id: str) -> User:
        user = User.query.get(user_id)
        if not user or user.is_deleted:
            raise ValueError("User not found")
        return user
