from datetime import datetime, timezone
from uuid import uuid4
from decimal import Decimal
from integration.db import db


class ProductModel(db.Model):
    """SQLAlchemy model for Product persistence"""
    __tablename__ = "ddd_products"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    seller_id = db.Column(db.String(36), nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True, index=True)
    
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
        return f"<ProductModel(id={self.id}, name={self.name}, seller_id={self.seller_id})>"
