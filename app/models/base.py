from app.extensions import db
from datetime import datetime, timezone
import uuid


class BaseModel(db.Model):
    """Base model with common fields and methods"""

    __abstract__ = True

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = db.Column(
        db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )

    def save(self):
        """Save instance to database"""
        db.session.add(self)
        db.session.commit()
        return self

    def delete(self):
        """Delete instance from database"""
        db.session.delete(self)
        db.session.commit()

    def update(self, **kwargs):
        """Update instance with provided kwargs"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = lambda: datetime.now(timezone.utc)()
        db.session.commit()
        return self

    def to_dict(self):
        """Convert model to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            else:
                result[column.name] = value
        return result


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""

    deleted_at = db.Column(db.DateTime, nullable=True)

    def soft_delete(self):
        """Soft delete the instance"""
        self.deleted_at = lambda: datetime.now(timezone.utc)()
        db.session.commit()

    def restore(self):
        """Restore soft deleted instance"""
        self.deleted_at = None
        db.session.commit()

    @property
    def is_deleted(self):
        return self.deleted_at is not None
