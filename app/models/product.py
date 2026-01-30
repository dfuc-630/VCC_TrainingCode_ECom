from app.models.base import BaseModel, SoftDeleteMixin
from app.extensions import db
from decimal import Decimal


class Product(BaseModel, SoftDeleteMixin):
    __tablename__ = "products"

    seller_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id = db.Column(
        db.String(36),
        db.ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    name = db.Column(db.String(255), nullable=False, index=True)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    detail = db.Column(db.Text)
    description = db.Column(db.Text)
    original_price = db.Column(db.Numeric(15, 2))
    current_price = db.Column(db.Numeric(15, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0)
    version = db.Column(db.Integer, default=0, nullable=False) 
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    order_items = db.relationship("OrderItem", backref="product")

    def has_stock(self, quantity: int) -> bool:
        return self.stock_quantity >= quantity

    def deduct_stock(self, quantity: int):
        if not self.has_stock(quantity):
            raise ValueError(f"Insufficient stock for product {self.name}")
        self.stock_quantity -= quantity
        self.version += 1
        return self

    def add_stock(self, quantity: int):
        self.stock_quantity += quantity
        self.version += 1
        return self

    def to_dict(self):
        data = super().to_dict()
        data["original_price"] = (
            float(self.original_price) if self.original_price else None
        )
        data["current_price"] = float(self.current_price)
        return data
