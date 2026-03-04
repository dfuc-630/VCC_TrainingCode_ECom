from datetime import datetime, timezone
from uuid import uuid4
from app.extensions import db


class UserModel(db.Model):
    """SQLAlchemy model for User persistence"""
    __tablename__ = "users"
    
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(50), nullable=False, index=True)  # admin, seller, customer
    
    # Status flags
    is_active = db.Column(db.Boolean, default=True, index=True)
    deleted_at = db.Column(db.DateTime, nullable=True)
    
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
        return f"<UserModel(id={self.id}, email={self.email}, role={self.role})>"
