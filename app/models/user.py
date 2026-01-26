from app.models.base import BaseModel, SoftDeleteMixin
from app.extensions import db
from app.enums import UserRole
import bcrypt


class User(BaseModel, SoftDeleteMixin):
    __tablename__ = "users"

    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    role = db.Column(db.Enum(UserRole, name="user_roles"), nullable=False)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    wallet = db.relationship(
        "Wallet", backref="user", uselist=False, cascade="all, delete-orphan" # 1 User - 1 Wallet
    )
    products = db.relationship(
        "Product",
        backref="seller",
        lazy="dynamic",
        foreign_keys="Product.seller_id",
        cascade="all, delete-orphan",
    ) # User can be Seller and can has many products, 1 - N
    customer_orders = db.relationship(
        "Order", backref="customer", lazy="dynamic", foreign_keys="Order.customer_id"
    )
    seller_orders = db.relationship(
        "Order", backref="seller", lazy="dynamic", foreign_keys="Order.seller_id"
    )

    def set_password(self, password: str):
        self.password_hash = bcrypt.hashpw(
            password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, password: str) -> bool:
        return bcrypt.checkpw(
            password.encode("utf-8"), self.password_hash.encode("utf-8")
        )

    def has_role(self, role: str) -> bool:
        return self.role == role

    def to_dict(self, include_sensitive=False):
        data = super().to_dict()
        if not include_sensitive:
            data.pop("password_hash", None)
            data.pop("deleted_at", None)
        return data
