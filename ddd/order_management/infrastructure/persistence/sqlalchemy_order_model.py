from datetime import datetime, timezone
from uuid import uuid4
from decimal import Decimal
from integration.db import db


class OrderModel(db.Model):
    """SQLAlchemy model for Order persistence"""
    __tablename__ = "ddd_orders"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    order_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.String(36), nullable=False, index=True)
    seller_id = db.Column(db.String(36), nullable=False, index=True)
    
    # Address & Contact
    shipping_address = db.Column(db.String(500), nullable=False)
    shipping_phone = db.Column(db.String(20), nullable=False)
    
    # Order totals
    total_amount = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    
    # Status
    status = db.Column(db.String(50), nullable=False, index=True)  # pending, confirmed, shipping, completed, cancelled, failed
    payment_status = db.Column(db.String(50), nullable=False, default="unpaid")  # unpaid, paid, refunded
    
    # Error tracking
    error_message = db.Column(db.Text, nullable=True)
    retry_count = db.Column(db.Integer, default=0)
    
    # Relationships
    items = db.relationship('OrderItemModel', cascade='all, delete-orphan', lazy='joined')
    
    # Timestamps
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    def __repr__(self):
        return f"<OrderModel(id={self.id}, order_number={self.order_number}, status={self.status})>"


class OrderItemModel(db.Model):
    """SQLAlchemy model for OrderItem persistence"""
    __tablename__ = "ddd_order_items"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    order_id = db.Column(db.String(36), db.ForeignKey('ddd_orders.id'), nullable=False)
    
    product_id = db.Column(db.String(36), nullable=False, index=True)
    product_name = db.Column(db.String(255), nullable=False)
    
    # Pricing
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    
    # Item status
    status = db.Column(db.String(50), nullable=False)  # pending, reserved, failed, completed, cancelled
    processing_at = db.Column(db.DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    
    def __repr__(self):
        return f"<OrderItemModel(id={self.id}, product_id={self.product_id}, quantity={self.quantity})>"
