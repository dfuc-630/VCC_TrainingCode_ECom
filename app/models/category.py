from app.models.base import BaseModel
from app.extensions import db


class Category(BaseModel):
    """Category model"""
    __tablename__ = 'categories'
    
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    
    # Relationships
    products = db.relationship('Product', backref='category', lazy='dynamic')