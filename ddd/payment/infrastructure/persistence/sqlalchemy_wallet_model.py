from datetime import datetime, timezone
from uuid import uuid4
from decimal import Decimal
from integration.db import db


class WalletModel(db.Model):
    """SQLAlchemy model for Wallet persistence"""
    __tablename__ = "ddd_wallets"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id = db.Column(db.String(36), unique=True, nullable=False, index=True)
    balance = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    is_active = db.Column(db.Boolean, default=True)
    
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
        return f"<WalletModel(id={self.id}, user_id={self.user_id}, balance={self.balance})>"
