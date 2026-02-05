from click import DateTime
from app.models.base import BaseModel
from app.extensions import db
from decimal import Decimal
from app.enums import OrderStatus, PaymentStatus, OrderItemStatus


class Order(BaseModel):
    __tablename__ = "orders"

    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=False, index=True
    )
    seller_id = db.Column(
        db.String(36), db.ForeignKey("users.id"), nullable=False, index=True
    )
    total_amount = db.Column(db.Numeric(15, 2), nullable=False)
    status = db.Column(db.Enum(OrderStatus, name="order_statuses"), default="pending")
    payment_status = db.Column(
        db.Enum(PaymentStatus, name="payment_statuses"), default="unpaid"
    )
    shipping_address = db.Column(db.Text)
    shipping_phone = db.Column(db.String(20))

    # Relationships
    items = db.relationship(
        "OrderItem", backref="order", lazy="dynamic", cascade="all, delete-orphan"
    )
    wallet_transactions = db.relationship("WalletTransaction", backref="order")

    def calculate_total(self):
        total = sum(item.subtotal for item in self.items)
        self.total_amount = total
        return total

    def can_cancel(self) -> bool:
        return self.status in ["pending", "confirmed"]

    def to_dict(self, include_items=False):
        data = super().to_dict()
        data["total_amount"] = float(self.total_amount)
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data


class OrderItem(BaseModel):
    __tablename__ = "order_items"

    order_id = db.Column(
        db.String(36),
        db.ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = db.Column(
        db.String(36),
        db.ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    product_name = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric(15, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(15, 2), nullable=False)
    status = db.Column(db.Enum(OrderItemStatus, name="order_item_statuses"), default="pending")
    processing_at = db.Column(DateTime, nullable=True)
    def calculate_subtotal(self):
        self.subtotal = self.price * self.quantity
        return self.subtotal

    def to_dict(self):
        data = super().to_dict()
        data["price"] = float(self.price)
        data["subtotal"] = float(self.subtotal)
        return data
